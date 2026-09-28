# Collaborator Substitution Pilot — Codex, Blind Tier-5 Retest Analysis

**Status:** EXPERIMENT ATTEMPTED, NOT COMPLETED. Environment limitation (Codex account usage quota), not a capability result. No substitution evidence — for or against — was produced. This document records the design and the failure honestly rather than discarding it or substituting a different, unplanned task.

---

## 1. Objective

Test the architectural claim "FeralEcho can substitute another capable collaborator for Claude on at least some important long-horizon evidence-first research tasks" empirically, via a blind substitution experiment: give Codex the same raw evidence Claude had for a real, already-completed research task, withhold Claude's conclusion, and compare independently.

This document reports what was actually attempted and what actually happened — **the experiment did not reach the point of producing a Codex output to evaluate**, so Phases 7-10 (scoring, blind comparison, substitution classification) could not be performed on real data. Per this mission's own stated standard, "we do not yet have evidence that we can switch" is a legitimate, useful result, and this document reports exactly that, without inflating a quota failure into a capability verdict.

---

## 2. Selected task (Phase 1)

**Task**: independently analyze the raw N=20 paired Tier-5 Council retest data (`audits/tier5_retest/tier5_retest_results.jsonl` and companion files) and determine: exact sample size and per-condition accuracy; the full discordant-pair breakdown; the correct paired statistical test and its result; whether the experiment's design could reach significance at all given its observed discordance; whether direct log evidence exists that the tested mechanism actually fired; and what the evidence does/does not establish, kept explicitly separate.

**Why this task was selected**, against the mission's own 9 criteria:
1. Claude previously performed it — yes, twice (`audits/2026-09-13_tier5_council_correctness_retest.md`, then independently re-verified in `audits/2026-09-14_tier5_retest_adversarial_audit.md`).
2. Substantial evidence available — yes, a complete raw 40-row results file plus full execution logs.
3. Meaningful architectural/engineering conclusion — yes, it directly informed a real "retain the Tier-5 fixes" decision.
4. Independently evaluable — yes, the core answer is checkable arithmetic/statistics (McNemar's test on a real 2×2 table), not just architectural opinion.
5. Small enough for one controlled session — yes, 40 data rows plus a few log files.
6. Not trivial — no, it requires computing a real statistical test correctly, reasoning about power/significance given a small discordant-pair count, and searching logs for mechanism-level evidence rather than trusting the surface pass/fail column.
7. Doesn't require proprietary information Codex lacks — confirmed, all evidence is plain text already in the repository.
8. Doesn't require exposing secrets — confirmed, none of the evidence set contains credentials.
9. Sufficient evidence for a fair independent investigation — yes.

This is exactly the "adversarial verification" / "determining what can and cannot be established from available evidence" archetype the mission brief asked to prefer, and it has the added advantage (over most other candidate tasks from this session) of resting on objective, checkable ground truth rather than purely architectural judgment.

---

## 3. Blindness design (Phases 2-4)

An isolated evidence directory was constructed outside the FeralEcho repository (in the operator's scratch space), containing only:

- `app/core/river_deliberation.py`, `echo_model_orchestrator.py`, `code_verification.py`, `echo_core.py`, `predictive_loop.py` — source for optional cross-file tracing.
- `scripts/run_tier5_retest.py`, `tier5_retest_task_pool.py`, `run_capability_pilot.py`, `verify_synthesis_refactor_control.py`, `verify_synthesis_refactor_live.py` — the real driver and its dependencies.
- `audits/tier5_retest/tier5_retest_results.jsonl`, `tier5_retest_progress.txt`, `tier5_retest_stdout.log`, `tier5_retest_task_pool_FROZEN.py`, `tier5_retest_task_pool.hash.txt` — the raw evidence.
- `audits/tier4_confirmatory_report.md`, `audits/tier5_refactor_report.md` — legitimate prior context (the original Tier-4 finding and the Tier-5 fix rationale that motivated this retest; both predate and do not reveal the retest's own outcome).

**Deliberately excluded**: `audits/2026-09-13_tier5_council_correctness_retest.md` and `audits/2026-09-14_tier5_retest_adversarial_audit.md` (Claude's own conclusions), and — caught during setup, not assumed safe — `audits/tier5_retest/MANIFEST.md`, whose own summary table states the aggregate result and the "not the 1/20 the original report credited" mechanistic finding directly. The entire research ledger (`research/FINDINGS.md`, `research/OPEN_QUESTIONS.md`) was excluded rather than surgically redacted, since it also states the conclusion (R-011/Q-010) and wasn't needed for the bounded task.

**Verified, not assumed**: a full case-insensitive content grep across the isolated tree for every conclusion-revealing term (exact percentages, "McNemar," "inconclusive," "0.0625," "3/20 tasks," the manifest's own language, etc.) found only two classes of false-positive matches, both confirmed harmless by direct inspection: (1) `[17/20]`/`[18/20]`-style literal task-progress counters in the raw log (task 17 of 20, task 18 of 20 — not pass-rate figures); (2) legitimate mentions of "McNemar"/"inconclusive" in the two background reports describing **Tier-4's own** historical result and methodology, not the retest's.

A private incumbent record (Claude's real conclusion, the known ground-truth numbers, and the evaluation criteria) was written to a file **outside** the directory Codex could access, per Phase 2's requirement.

The task specification given to Codex (`TASK.md`, passed as the prompt, not left as a discoverable file inside the evidence directory) used neutral wording throughout (e.g., "determine whether... was capable of reaching... significance," not "verify that it couldn't") and explicitly told Codex it was free to disagree with any implicit framing.

---

## 4. Candidate environment (Phase 4/5 details)

- **Codex CLI version**: 0.154.0 (confirmed via `codex --version` before running).
- **Authentication**: logged in via ChatGPT (subscription-based), confirmed via `codex login status` before running — this matters because the mission's own safety boundary required explicit approval before *paid API calls*; a subscription-quota invocation is the same usage model this Claude Code session itself runs under, not a separate metered charge, so it was judged not to require a separate approval gate. This judgment call is disclosed here explicitly, not assumed silently.
- **Execution mode**: `codex exec` (non-interactive), `--sandbox workspace-write` (scoped to the isolated evidence directory only, no access to the real FeralEcho repository), `--skip-git-repo-check` (the isolated directory is not a git repository), `--json` (structured event log), `-C <isolated dir>` (working root), `-o <file>` (final-message capture).
- **Network access**: none granted or attempted beyond Codex's own API calls to its own backend.
- **Start time**: 2026-09-14 11:12:10 PDT (real, captured wall-clock timestamp).

---

## 5. What actually happened (Phase 5 result)

The Codex session started (`thread.started`, `turn.started` events both fired, confirming the isolated environment and prompt were successfully delivered) and then failed immediately, before producing any analysis:

```
{"type":"error","message":"You've hit your usage limit. To continue using Codex and get access to
GPT-5.3-Codex, start a free trial of Plus today (https://chatgpt.com/explore/plus), or try again at
Oct 9th, 2026 11:58 PM."}
{"type":"turn.failed","error":{"message":"You've hit your usage limit. ...try again at Oct 9th, 2026 11:58 PM."}}
```

End time: 2026-09-14 11:12:14 PDT — a 4-second run, consistent with an immediate quota rejection rather than any real attempt at the task. No `CODEX_ANALYSIS.md` was written (confirmed: no files newer than the task specification exist anywhere in the isolated evidence directory). No `codex_final_message.txt` was produced.

**Classification of this failure, per this mission's own Phase 12 requirement to distinguish causes rather than blame the model**: this is an **ENVIRONMENT LIMITATION** (account usage quota, resetting per the error message's own stated date of Oct 9, 2026) — not a collaborator-capability finding, not an experimental-design flaw, not a prompt-limitation, and not a tool-limitation in the sense of Codex being unable to do the work. Codex was never given the opportunity to attempt the task at all.

---

## 6. Preserved raw evidence (Phase 6)

- `codex_run.log` — full stdout/stderr of the invocation, including the exact JSONL error events quoted above.
- The isolated evidence directory itself (`TASK.md` plus the full blind evidence set) — preserved unmodified, in the operator's scratch space, not the FeralEcho repository.
- No candidate substantive output exists to preserve, because none was produced.

---

## 7-10. Scoring, blind comparison, disagreement analysis, substitution classification

**Not performed.** There is no Codex output to score against the 10 evaluation criteria, nothing to blind-compare against Claude's original conclusion, and no disagreement to analyze. Producing scores or a comparison table here would misrepresent an untested quota failure as an evaluated result — exactly the kind of overclaim this whole research program's own standing discipline exists to prevent.

---

## 11. Resource cost (Phase 11)

- Elapsed wall-clock time: ~4 seconds of actual Codex execution; the surrounding setup (task selection, blind-environment construction, leak verification) took considerably longer but is reusable for a retry.
- Model calls: 1 attempted, 0 completed (rejected at the quota gate before generating any tokens).
- Paid API cost: **$0** — the invocation used the existing ChatGPT subscription's quota allocation, which is now exhausted for the current billing period per the error message.
- Human interventions: none required during the run itself (it failed too fast to need any).

---

## 12. Falsification discipline (Phase 12)

Applying the mission's own required distinction directly: **could the task selection, evidence packaging, environment, prompt, or tool availability have unfairly disadvantaged Codex?** Yes, in one specific, identifiable way — the account's usage quota was already exhausted or exhausted by this single call, which is a pre-existing account-state condition entirely independent of the task design, the blindness construction, or Codex's own capability. This is explicitly **not** evidence that Codex would have failed or succeeded at the task; it is evidence that this particular attempt, under this particular account's current quota state, could not run.

**Could the result appear to show failure for a reason unrelated to collaborator capability?** Yes — and that is exactly what happened. This section exists specifically to prevent the natural but wrong inference "Codex failed the task" from this result. The correct statement is "this attempt could not be run."

---

## 13. Substitution classification (Phase 10, formally)

Per the mission's own defined scale (S0-S3), none of the four categories accurately describes this outcome — S0 ("Codex could not perform the task adequately") implies an actual attempt and an actual inadequate result, which did not happen here. The honest classification is:

**UNKNOWN / NOT YET TESTABLE** — no evidence was generated, in either direction. This is explicitly one of the two legitimate outcomes the mission itself names as useful ("we do not yet have evidence that we can switch" vs. "we have evidence that we can") — it is the honest result, not a placeholder for a better one.

---

## 14. Generalization limits

None established — there is nothing to generalize from.

---

## 15. Reproducibility implications

The experimental design itself (task selection, blindness construction, leak-verification methodology, task specification wording) is fully reusable and does not need to be redone. Only Phase 5 (the actual Codex invocation) needs to be retried, either after the quota resets (per the error message, on or after Oct 9, 2026) or under a different authenticated account/plan, if one becomes available and is explicitly approved.

---

## 16. Strategic dependency implications

One real, if narrow, finding stands on its own regardless of the failed run: **Codex, under its current account authentication, is itself subject to a hard usage ceiling that can be exhausted by a single research-scale request** (the same account this session confirmed, in the immediately preceding `research/FRONTIER_COLLABORATOR_REGULATORY_DEPENDENCY.md` mission, is architecturally undemonstrated for FeralEcho's actual heaviest dependency — long-horizon agentic research work). This pilot's own failure is a small, live, concrete illustration of exactly the account-tier/quota-restriction failure mode that document's Phase 5 already asked about in the abstract ("usage becomes substantially more expensive," "rate limits increase") — now observed directly, on this exact account, rather than only theorized.

---

## 17. Follow-up experiment

Retry this exact experiment (same task, same blindness design, same evaluation criteria — all preserved in this document and in the untouched isolated evidence directory) once Codex quota is available again, either via the natural reset date or an explicitly-approved different access path. Do not select a new task merely because this one stalled — the design survives the failure and should be reused, not redesigned.

---

## 18. Repository impact

- Files created: exactly this one document, `research/COLLABORATOR_SUBSTITUTION_CODEX_PILOT.md`. All experimental artifacts (isolated evidence directory, task specification, incumbent record, Codex run log) live in the operator's scratch space, outside the FeralEcho repository, and were not copied in.
- Git HEAD before and after: `2fba42644c82b9f7096276f4dd338d615cf1bcce`, unchanged (verified via direct `git rev-parse HEAD` before this mission started and again after this document was written).
- Working-tree path count: 139 before this mission's own actions; 140 after, which is exactly this one new untracked file — confirmed by direct `git status --short` recount, not assumed. The experiment itself (the isolated directory, the Codex invocation) made zero writes to the FeralEcho repository.
- No production code, `memory/`, relay infrastructure, or provider configuration was touched.
- No commit, no push, no restart.
- No paid API call was made — the attempted call was rejected before any billable generation occurred, per the account's own subscription quota.
