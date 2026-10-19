# Previous-outcome replay — 2026-10-19

Canonical continuation of `audits/2026-10-19_recursive_learning_baseline.md`. That baseline is unchanged. This file records the experiment the baseline specified and did not run.

Run time: 2026-10-19T03:20:22Z. Machine: M5. Cash cost: $0. Model calls: 0. Production files written: none.

Raw result: `audits/2026-10-19_previous_outcome_replay_result.json` (15,904 bytes, sha256 `9923d6c8806ef0092c9418835d8d441f62812145eac5103b8a380e7522d236bf`).
Instrument: `audits/2026-10-19_previous_outcome_replay.py`. It reads `memory/experiments/persistent_routing/` and does not import `app.core`. It does not open `memory/river_brain.pkl`.

## Question and scope

Can a lookup table that has seen the pass or fail of its own earlier prompting attempt choose a better prompting strategy on held-out tasks than two controls: always using the plain prompt, and the same table fed shuffled labels?

Scope of this run: the three sealed lineages already stored under `memory/experiments/persistent_routing/` (lineages 0, 1, and 2), arm C teaching rows only, historical holdout yes/no grades only. Strategies are `DIRECT`, `STEPWISE`, and `WORKED_EXAMPLE`. The extra situation field is `previous_outcome` in `{none, pass, fail}`, taken from the latest teaching attempt in the same `(arg_count_bucket, input_shape)` bucket. Holdout outcomes never fill that field. Exam policy is greedy. Shuffle seed is `20261019`, one shuffle, lineages 0 then 1 then 2.

This is the previous-outcome replay from the baseline's Deliverable 4. The rules below were copied from that document before this run and were not changed after the numbers were seen.

## What was already verified before the run

Facts, checked by directory listing and file reads, then by this script's own census:

- The strategy records exist. Arm C has 18 teaching rows (6 per lineage). Each lineage has 4 holdout tasks. Signatures recomputed from `sig`/`spec` matched the logged holdout signatures on every exam (`sig_ok` true on all 12).
- Arm B holdout files chose `DIRECT` on all 12 tasks.
- The original selector's empty-state hash is sha256 of `{}` = `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`. The replay starts from that hash.
- Historical holdout files store a yes/no only for the strategy that was actually executed. A choice with no stored grade is unscorable. The script does not invent a grade.

Lineage 0's teaching sequence was re-derived by hand from `log_E_experience.jsonl` after the script printed its table. The printed means match that sequence. The script is not forcing `DIRECT` by a bug.

## Frozen rule

Pass, all of these: real labels beat always-`DIRECT` by at least one scored holdout pass, at least one holdout decision changes, real labels beat the shuffled arm, the empty-row count is not the whole holdout, and a fresh process would repeat the choice.

Fail, any of these: real labels do not beat always-`DIRECT`; shuffled labels do as well; no situation tried two strategies; every holdout row is empty.

A missing grade counts as unscorable and as 0 passes. It is not filled in from another strategy.

## Result

`pass_rule_met`: false.

| Arm | Passed | Scored | Unscorable | Conflict | Holdouts |
|---|---:|---:|---:|---:|---:|
| Always DIRECT | 4 | 12 | 0 | 0 | 12 |
| Real labels | 4 | 12 | 0 | 0 | 12 |
| Shuffled labels | 4 | 9 | 3 | 0 | 12 |

Decisions changed from `DIRECT` under real labels: 0.
Empty real-label holdout rows: 3 of 12 (every `K2.S1`, signature `1|dict`, which never appeared in teaching).
Teaching updates: 18.
Coarse buckets in which two strategies were tried: 1 (`1|tuple`, lineage 0 only).
New keys in which two strategies were tried: 1 (`1|tuple|fail`, lineage 0 only).
Arm B uniformly `DIRECT`: true.

Fail reasons recorded by the script:

- Real labels did not beat always-`DIRECT` by one scored pass.
- Shuffled labels did as well on the scored rows (4 and 4). The three shuffled rows that switched strategy have no historical grade, so they cannot be counted as wins for either arm.
- No holdout decision changed.

The two-strategy count is not zero, and 9 of 12 real-label rows were populated. Those two fail clauses did not fire. The result fails on the benefit clauses.

### Per-holdout exam

`prev` is the real-label previous outcome. Every real choice was `DIRECT`. `changed` is false on every row.

| Lineage | Task | Signature | prev | DIRECT passed | Real choice | Real passed | Shuffle choice | Shuffle grade |
|---|---|---|---|---|---|---|---|---|
| 0 | K2.S1 | 1, dict | none | yes | DIRECT, empty row | yes | DIRECT | scored, yes |
| 0 | K2.S2 | 1, tuple | fail | no | DIRECT | no | WORKED_EXAMPLE | unscorable |
| 0 | K2.S3 | 1, tuple | fail | no | DIRECT | no | WORKED_EXAMPLE | unscorable |
| 0 | K2.S4 | 1, tuple | fail | no | DIRECT | no | WORKED_EXAMPLE | unscorable |
| 1 | K2.S1 | 1, dict | none | yes | DIRECT, empty row | yes | DIRECT | scored, yes |
| 1 | K2.S2 | 1, tuple | fail | no | DIRECT | no | DIRECT | scored, no |
| 1 | K2.S3 | 1, tuple | fail | yes | DIRECT | yes | DIRECT | scored, yes |
| 1 | K2.S4 | 1, tuple | fail | no | DIRECT | no | DIRECT | scored, no |
| 2 | K2.S1 | 1, dict | none | no | DIRECT, empty row | no | DIRECT | scored, no |
| 2 | K2.S2 | 1, tuple | fail | no | DIRECT | no | DIRECT | scored, no |
| 2 | K2.S3 | 1, tuple | fail | yes | DIRECT | yes | DIRECT | scored, yes |
| 2 | K2.S4 | 1, tuple | fail | no | DIRECT | no | DIRECT | scored, no |

Pooled by task, always-`DIRECT` historical grades: `K2.S1` passed 2/3, `K2.S2` passed 0/3, `K2.S3` passed 2/3, `K2.S4` passed 0/3.

Twelve decisions. The pass-count gap is 0. A confidence interval around a difference of 12 binary trials is wide. The decision column is tighter than the pass count: the real-label policy and the always-`DIRECT` policy selected the same strategy on every row, so their pass counts are the same grades, not two noisy samples that happened to tie.

### Why the table stayed on DIRECT

Arm C strategy counts from `log_E_experience.jsonl`:

- Lineage 0: `DIRECT` pass 3, `DIRECT` fail 2, `WORKED_EXAMPLE` fail 1. `STEPWISE` was never used.
- Lineage 1: `DIRECT` pass 4, `DIRECT` fail 2. No other strategy.
- Lineage 2: `DIRECT` pass 4, `DIRECT` fail 2. No other strategy.

Lineage 0 real-label table after the replay (content hash `d897c5b39eddd5c65d21852c7f3f4a6aa573ff86b64ef840565d4f4889865930`):

| Key | Strategy | Count | Mean |
|---|---|---:|---:|
| `1\|tuple\|none` | DIRECT | 1 | 1.0 |
| `1\|tuple\|pass` | DIRECT | 2 | 0.0 |
| `1\|tuple\|fail` | DIRECT | 1 | 1.0 |
| `1\|tuple\|fail` | WORKED_EXAMPLE | 1 | 0.0 |
| `2\|tuple\|none` | DIRECT | 1 | 1.0 |

The holdout tuple tasks look up `1|tuple|fail`. `DIRECT`'s mean there is 1.0 and `WORKED_EXAMPLE`'s mean is 0.0, so greedy stays on `DIRECT`. That is the legal "do nothing" outcome the protocol allowed. Lineages 1 and 2 have the same hash as each other (`ef4b6b5925f4a5ecf25aa9f1e2449d30155d861873ab2db6d6853eb6cd57079f`) and only `DIRECT` in every cell, so they also stay on `DIRECT`.

The shuffled arm's three switches are lineage 0, tasks `K2.S2`–`K2.S4`, choice `WORKED_EXAMPLE`. Under the shuffled labels the single `WORKED_EXAMPLE` attempt is the one success stored on `1|tuple|fail`, so greedy picks it. No holdout file grades `WORKED_EXAMPLE`. Those three rows stay unscorable. Lineages 1 and 2 only ever stored `DIRECT`, so shuffling their labels cannot create another strategy.

Fresh-process reload was specified only if the pass rule was met. It was not run.

## What this establishes

Demonstrated, inside this scope:

- Adding `previous_outcome` to the situation key does not change any of these 12 holdout choices.
- The real-label pass count stays 4, the same as always-`DIRECT`.
- The one cell that actually compared two strategies preferred `DIRECT` (1/1 versus 0/1).
- The September selector's "stored state, unchanged holdout choice" result is not explained by the missing previous-outcome bit. With that bit present, the choice is still `DIRECT`.

Falsified within this scope:

- The hypothesis that this one extra field would make the table beat always-`DIRECT` and beat a shuffled table on these traces.

Unknown, left unknown on purpose:

- Whether `STEPWISE` or `WORKED_EXAMPLE` would have passed `K2.S2` or `K2.S4`. Those strategies were not executed on the holdout. `STEPWISE` has zero arm-C attempts. `WORKED_EXAMPLE` has one teaching failure (`K2.T3`, lineage 0). The execution log stores code hashes, not the code or the oracle's error text.
- Whether some other situation key, some other task family, or a policy that forces every strategy to be tried would do better. This run does not speak to that.
- Level 4 in the baseline's sense (a measured strategy outcome changing a later strategy choice, with a higher holdout pass rate). This run does not establish it.

A stored mean changed. That is not a learning gain. The choice and the pass count stayed with the plain prompt.

## Hypothesis update

Before the run, the leading local explanation of the September null result was that the situation key never saw the previous outcome. That explanation is now the weaker one for these traces. The stronger account of this file is sparsity: 17 of 18 teaching attempts were `DIRECT`, the single alternative failed once, and the holdout lookup therefore had a higher mean for `DIRECT`.

The baseline's own shelf rule applies: if the richer key still ties always-`DIRECT`, or ties a shuffled table, the 17 September 12-family pilot stays on the shelf. Both ties happened. The pilot was not started.

## Resource constraints at the time of the decision to stop

- Cash: $0 spent, $0 required for this result.
- Compute: one local Python process, standard library only, under a second.
- Live server: `python -u run.py` PID 30479 was listening on port 5000, RSS about 1.1 GB, elapsed about 7 hours 54 minutes. It was not restarted.
- Swap: `vm.swapusage` reported total 4096.00M, used 3289.56M, free 806.44M.
- Ollama had `deepseek-r1:7b` resident (about 5.4 GB). `qwen2.5-coder:7b` was not the loaded model.
- A follow-up generation burst would have loaded another 7B model beside that resident model and the live server. That is an operational risk on this machine's existing crash history, and it is not a request for new hardware.

## Why the sequence stops

The pre-registered fail rule says a fail ends the sequence. It is not followed by a controller, a second feature, or a production patch.

Two later experiments were considered and not run:

1. The 12-family outcome-to-selector pilot. It is the larger version of the same idea. The baseline says to leave it on the shelf when this replay ties. Running it because the protocol already describes it would ignore that shelf rule.
2. Eight new local generations (`STEPWISE` and `WORKED_EXAMPLE` on the four holdout tasks) to ask whether any untried prompt passes the tasks `DIRECT` missed. That would classify coverage. It would not show the system learning to select a strategy. The grades required to score the frozen rule already exist for every real-label choice. Swap was 3.3 GB of 4 GB used. The generations were not worth that operational cost tonight.

Stopping condition for this hypothesis: meaningfully falsified on these 12 holdouts, and no justified next experiment remains for this selector shape (condition B of the mission). The wider question, whether some other zero-cost mechanism could learn from its own learning, stays open. This file does not call that question impossible.

## Single best next action

None for this selector. Leave production as it is. Leave the 12-family pilot on the shelf. Do not add another situation field. Do not build a controller.

If a later session reopens coverage, the only bounded check that matches the leftover unknown is: the same worker settings already frozen in the baseline (`qwen2.5-coder:7b`, temperature 0.2, `num_predict` 512, `num_ctx` 4096), strategies `STEPWISE` and `WORKED_EXAMPLE`, tasks `K2.S1`–`K2.S4`, isolated from production, and only when swap headroom is real. A pass there would mean an untried prompt can solve a task the plain prompt missed. It would still not be evidence that a learned selector found that prompt.

## Explicitly not done

- No edit to `app/`, `run.py`, the nudge, the liveness ledger, or governance files.
- No write to `memory/river_brain.pkl` or to the persistent-routing logs.
- No fresh-process reload, because the pass rule failed.
- No second shuffle.
- No post to the Ark mailbox.
- No commit.
