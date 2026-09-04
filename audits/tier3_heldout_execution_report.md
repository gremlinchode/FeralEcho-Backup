# FeralEcho: Tier-3 Held-Out Experiment — Forensic Execution Report

**The held-out experiment was executed exactly once. No held-out task content was inspected before execution. No
retries, cherry-picking, seed changes, parameter changes, model changes, or apparatus changes occurred at any
point — before, during, or after seeing results.** This report documents the execution process only; it does not
interpret the scientific result beyond what the collected data supports (per explicit instruction, the
scoring/spot-check/unblinding analysis is separate, future work).

## 1. Pre-Run Telemetry (captured immediately after handoff confirmation)

| Signal | Reading | Threshold | Result |
|---|---|---|---|
| `ollama ps` resident models | **0** | ≤1 | PASS |
| Load average (1/5/15 min) | 1.88 / 1.84 / 1.70 | ≤2.0 (1-min) | PASS |
| `llama-server` subprocesses | none running | — | PASS |
| Watchdog log recency | last real activity 13:09:17 (a clean, completed synthesis, not a truncated/dangling one); 1m49s of silence before this capture, zero new lines | — | PASS |
| `run.py` process | confirmed stopped (per user handoff, independently re-verified via `ps aux`) | — | PASS |
| Additional contamination control (user-initiated, noted for the record) | The sibling Echo instance on the MacBook Air ("Arch") was independently stopped by the user specifically so no cross-machine `/message/receive` traffic could reach this M5 instance during the run | — | Noted |

## 2. Gate Decision

# WINDOW_STATUS = CLEAR

Zero resident models, zero active or lingering generation processes, load average comfortably under threshold,
and direct confirmation (via `run.py`'s absence) that autonomous loops were structurally incapable of firing —
not merely quiet. This is the cleanest environment reading obtained at any point across this entire investigation.

## 3. Held-Out Hash Verification

- **Expected**: `2d78cbdb3657755f65779d010590ae348ded22d6d32d300bddacfd0aaa0e912a`
- **Live (immediately before execution)**: `2d78cbdb3657755f65779d010590ae348ded22d6d32d300bddacfd0aaa0e912a`
- **Match**: ✅ Exact.
- Hash verification only — no task content was printed, enumerated, previewed, summarized, or copied at any point
  before execution.

## 4. Exact Execution Command

```
python3 scripts/run_tier3_apparatus.py --heldout
```

Run from the repository root, `scripts/run_tier3_apparatus.py` unmodified at execution time (file mtime predates
the run start).

## 5. Confirmation of Single Execution

- Process launched once, PID 74792, started 13:11 local time.
- Process confirmed exited cleanly (`ps aux` shows no trace post-completion), exit code 0.
- **Result file contains exactly 32 records** — 8 held-out tasks × 4 arms, the complete, expected set, with no
  duplicates and no gaps (verified: all 8 `held_0X` task IDs present exactly 4 times each, one per arm).
- No second invocation of this command occurred at any point during this session.
- Total wall-clock span of the run, computed from the first and last record's own real timestamps: **565.2
  seconds (9.4 minutes)** — consistent with, and a direct further confirmation of, the genuinely low-contention
  environment (dramatically faster than this project's own repeated historical experience under contention,
  where individual `ARCH_COUNCIL` candidates alone had taken up to 7+ minutes each).

## 6. Per-Arm Call Accounting

| Arm | Generative calls (recorded `total_calls`) | Real underlying `_ollama_query()` calls | Consistency across all 8 real candidates |
|---|---:|---:|---|
| `BASE_1` | 1 | 1 | 8/8 identical |
| `BASE_N` | 4 | 4 | 8/8 identical |
| `ARCH_PIPELINE_ISOLATED` | 1 | 1 | 8/8 identical |
| `ARCH_COUNCIL` | 4 | **5** | 8/8 identical — see §7 |

- **Model pinning**: 100% consistent — every `BASE_1`/`BASE_N`/`ARCH_PIPELINE_ISOLATED` record (24 total) used
  `qwen2.5-coder:7b`, with zero drift across the entire run.
- **`max_tokens`**: uniformly `2048` across all 32 records, no exceptions.
- **Council composition**: identical across all 8 real `ARCH_COUNCIL` executions — councillors
  `['qwen2.5-coder:7b', 'mlx:qwen3', 'echo:latest']`, synthesis by `echo:latest`, every single time. This is a
  real, honest observation about this specific run, not a claim about what *would* happen in general — recorded
  because it is what actually occurred, not because it was expected.
- **Real ground truth (truncation attribution)**: present for all 32/32 records — the Objective-1 truncation
  repair and the `ARCH_PIPELINE_ISOLATED` fix both held completely through real execution, not just in prior
  synthetic verification.
- **Isolation / no production contamination**: the `side_effects_so_far` counter advanced by exactly +4 on each
  of the 8 real `ARCH_COUNCIL` executions (32 total, matching exactly) and by **zero** across all 24 combined
  executions of the other three arms — confirmed directly from the real run's own data, not assumed from prior
  testing.

## 7. `ARCH_COUNCIL` Warm-Up Disclosure

**`ARCH_COUNCIL` performed 5 real `_ollama_query()` calls per candidate, not 4, in every one of its 8 real
executions this run** — confirmed directly from the recorded `total_real_ollama_calls_including_warmup` field
(value: 5, all 8 times, zero exceptions). The 5th call is a real, unconstrained-length warm-up ping to the
synthesis model (`echo:latest`), issued by production's own `river_deliberation._warm_up_echo()` before the real
council loop begins. Its own response content is always discarded — never fed into synthesis, never scored — but
its wall-clock/compute cost is real and is included in `ARCH_COUNCIL`'s own recorded `generation_time` (since it
happens inside the same timed call). **This asymmetry was not removed, bypassed, or compensated for in this run.**

**The four arms in this experiment are therefore NOT perfectly equal-call or perfectly equal-compute
conditions.** `BASE_1` and `ARCH_PIPELINE_ISOLATED` are genuinely single-call. `BASE_N` and `ARCH_COUNCIL` are
matched on *generative* call count (4 each) and on `max_tokens` per generative call (2048, uniform). `ARCH_COUNCIL`
additionally spends one real, extra, content-discarded call beyond that — a known, disclosed, un-eliminated
limitation of the currently-verified apparatus, not a new finding of this run (first caught during the prior
execution-gate mission), now directly confirmed present and consistent across every real held-out candidate.

## 8. Post-Run Telemetry

| Signal | Reading |
|---|---|
| `ollama ps` resident models | 0 (models unloaded after their own keep-alive expired post-run) |
| Load average (1/5/15 min) | 2.28 / 2.22 / 1.95 |
| Swap | 3255.12MB / 4096.00MB used |
| Leftover `run_tier3_apparatus`/`llama-server` processes | none |

The 1-minute load average reading nudged slightly above 2.0 by the time this post-run snapshot was taken (~14
seconds after the process exit) — consistent with ordinary short-term system noise following the run's own tail
end, not indicative of any problem with the completed run itself (the run's own data, per §6, shows no anomaly).

## 9. Execution Anomalies

**None.** Specifically checked and confirmed absent:
- Zero `error` fields populated across all 32 records.
- Zero `INFRASTRUCTURE_FAILURE` classifications (the pre-registered H5 override threshold of 15% was never
  approached — actual rate: 0%).
- Zero timeouts.
- Zero retries (none were permitted or attempted).
- Zero crashes (clean process exit, code 0).
- Zero model-identity drift.
- Zero call-count deviation from each arm's own established contract (beyond the already-known, disclosed
  `ARCH_COUNCIL` warm-up in §7).
- Zero evidence of cross-task contamination (side-effects counter progression is monotonic and exactly
  attributable to `ARCH_COUNCIL` alone, as expected).

## 10. Result Artifact Locations

- `audits/tier3_apparatus/heldout_results.jsonl` — the 32 raw result records (the experiment's own primary
  output).
- `audits/tier3_apparatus/held_out_task_suite.json` — the frozen 8-task suite (unmodified, hash-reverified
  before and, implicitly, unchanged after — the harness itself only ever reads this file).
- `/tmp/tier3_heldout_execution.log` — the full raw stdout/stderr of the run (ephemeral, not part of the durable
  repo record).

## 11. What This Experiment Can and Cannot Legitimately Establish

**This report does not attempt that analysis.** Per explicit instruction, no scientific interpretation is offered
here beyond the two boundary statements this whole investigation has already established and preserved verbatim:

> `ARCH_PIPELINE_ISOLATED` tests the isolated self-edit generation mechanism/framing, not Echo's literal current
> production self-edit call path.

> This four-arm design cannot separate heterogeneous model diversity from Council-specific orchestration as
> competing explanations for a Council win.

To these, this run adds one further, execution-specific boundary, established in §7:

> Any comparison involving `ARCH_COUNCIL`'s result must account for its real, disclosed 5-call budget (versus
> `BASE_N`'s 4), not treat the two as perfectly compute-matched.

**The raw data (32 records, complete, anomaly-free, call/model/token-budget accounting fully verified) is now
available for the separate, subsequent scoring/spot-check/unblinding pass** this investigation's own prior
protocol (`audits/current_capability_synthesis.md` §11) already lays out. That pass — computing the actual paired
comparisons, applying the pre-registered ≥25-percentage-point effect-size threshold, and reading the result
against H1/H2/H3/H4 — has not been performed in this report and is explicitly out of scope for it.
