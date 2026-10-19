# Later Outcome After Cost-Driven Retention

**Date:** 2026-10-19
**Type:** Investigation-only. One read-only measurement of existing logs, inside `memory/experiments/later_outcome_after_cost_20261019/`.

## Executive Verdict

The cost-on keep set showed a **lower** later exact-success rate than the cost-off keep set (VERIFIED). On held-out keeps whose prompt key was not one of the four keys that charged the budget, the next same-key self-edit result token is `success` for 140 of 349 cost-on rows that have a later token, and for 670 of 787 cost-off rows. The rates are 0.4011461318051575931232091691 and 0.8513341804320203303684879288. The difference, cost-on minus cost-off, is -0.4501880486268627372452787597. Integer cross-multiplication gives the same direction: 140 x 787 = 110180, and 670 x 349 = 233830.

All 335 no-formation-key refills lack a later token. Removing them leaves the same 140/349 and 670/787 counts, so the lower difference remains. Missing rows stay outside the denominator. This retention shift is not an outcome gain on the precommitted exact-success definition. The cost rule stays where the prior cost audit left it: a static integer budget, with no promotion.

## Question

Do the held-out retention decisions that changed under the already-run outcome-signal cost produce a higher rate of subsequent successful self-edit result tokens than the decisions made with the cost disabled, on prompt keys that were not the contrary signal used to charge the budget?

What would change the conclusion: equal cross-products would be no difference; a larger cost-on cross-product would be a higher rate. A zero present-count in either arm would make that arm's rate undefined. Either of those outcomes was an acceptable stop.

## Hypotheses

- H0: the later exact-success rates are equal.
- H_higher: the cost-on rate is higher.
- H_lower: the cost-on rate is lower.

The evidence favors H_lower on exact `success`. H0 and H_higher fail for that definition.

A secondary definition was locked before scoring and is reported separately: non-failure means the later token does not contain `fail` (case-insensitive) and the suffix after the result span has no non-empty `error:` field. Under that definition the cost-on rate is higher (327/349 versus 671/787, delta +0.0843579222538164951231145076). The two definitions disagree because 186 of the 349 cost-on later tokens are `rejected_meaningless_prompt`. That token is neither `success` nor a fail/error token. The headline follows exact `success`. The non-failure movement is not an outcome gain.

## Scope / Non-Goals

This measurement loads the frozen 5,125-row holdout traces from `memory/experiments/outcome_signal_cost_20261019/` and reads `memory/SELF_EDIT.log` only to locate the next result token. It writes inside the new experiment root and this audit.

It does not retune the budget, re-run `run_cost.py`, edit the cost root, edit the finished cost audit, or edit the ceiling note. It does not generate model output, install packages, alter production memory, FAISS, consolidation, selectors, governance files, or the Ark, reopen a closed branch, commit, or send a relay note. It does not promote the cost rule. It does not impute a success or a failure when a prompt key has no later token.

## Evidence Summary

| Claim | Label | Source | Justification |
|---|---|---|---|
| Cost-on later exact-success rate is 140/349; cost-off is 670/787; delta -0.4501880486268627372452787597; direction lower | VERIFIED | `verify_later.py` exit 0, `verify.json` `match: true`; recount of `scored_trials.jsonl` | Second process re-parsed the pinned log, recomputed both arms, and matched every stored later token |
| 420 cost-on and 92 cost-off scored rows have no later token | VERIFIED | same verifier tuple | Counted separately; excluded from both rates |
| Charging-key exclusion removes 28 cost-on and 146 cost-off keeps; charging-row exclusion removes 0 | VERIFIED | verifier excluded counts; trial recount | Four signal ids and four prompt keys; no keep row's own id is a charging-signal id |
| All 335 no-formation-key refills are missing; the success delta is unchanged after dropping them | VERIFIED | `verify.json` checks `n_335_present == 0` and `n_335_missing == 335`; `excluding_335_refills` in `result.json` | Present and success counts stay 349 and 140; cost-off stays 787 and 670 |
| Later-token histogram: cost-on success 140, rejected_meaningless_prompt 186, load_failed 12, staging_import_failed 10, invalid_syntax 1; cost-off success 670, load_failed 116, invalid_syntax 1 | VERIFIED | recount of `scored_trials.jsonl` after the verifier matched each later token to the log | Explains why non-failure rises while exact success falls |
| Overlap keeps are identical across arms (103/113). The gap sits in only-on 37/236 versus only-off 567/674 | VERIFIED | recount joining frozen keep traces to `scored_trials.jsonl` | Same later token for a row kept by both arms; the rate gap is the changed membership |
| Frozen cost artifacts and closed-branch hashes match the pre-measurement record | OBSERVED | SHA-256 at 2026-10-19T21:45:38Z | Listed in the integrity record |
| Live SELF_EDIT.log, FAISS, memory meta, and self_model moved during the window | OBSERVED | size and SHA-256 before the pin and again at 21:45:38Z | Live process appends. Prefix hash of the first 33,008,379 bytes is unchanged. This measurement pinned a byte count and did not write those files |
| Production `app/` does not reference this budget | OBSERVED | search of `app/**/*.py` for `outcome_signal_cost`, `BUDGET0`, and `later_outcome_after_cost` | No matches |
| The cost caused the lower success rate | UNKNOWN | keep sets differ before the later token is read | The comparison is between two different retained sets. Selection accounts for the recorded gap. Causation is not established |
| Row-skip sensitivity (keep the four charging keys) is also lower on exact success: 165/376 versus 802/932, delta -0.4216852342251849146196694366 | OBSERVED | `result.json` `row_skip_sensitivity` from `measure_later.py` | First script only. `verify_later.py` does not recompute this arm. The headline does not use it |

## Repository Archaeology

The retention rule under test already exists as a finished root-local script, `memory/experiments/outcome_signal_cost_20261019/run_cost.py`. Its traces, index, and `result.json` are on disk and were hashed before scoring. Nothing under `app/` imports that root or the new measurement root (OBSERVED). The rule is not reachable from the live server. The measurement executed once, as `measure_later.py`, and a second process, `verify_later.py`, re-derived the headline counts. Both writes stayed inside the experiment root. No production consumer reads the budget or these later-token rates (OBSERVED). The rate difference is real inside the measurement and has no downstream production effect.

## Runtime Trace

TRIGGER: the finished cost test had already changed keep/drop decisions (`decisions_differ: true` in the frozen cost `result.json`).

ENTRY POINT: `measure_later.py` reads the frozen traces and index, then reads `memory/SELF_EDIT.log`.

PROCESSING: holdout rows with `decision == keep`, separately for the active trace and the disabled trace. A keep whose prompt SHA-256 equals a charging-signal SHA-256 is excluded. The charging signals are the `prior_signal_id` values of active keeps with `charged == 5`: 20 charges, 4 distinct signal ids, 4 distinct prompt keys. Each of those signals is a formation row (`id % 5 != 0`) with a smaller id than the keep that cited it.

STATE CHANGE: none in production. The script writes `result.json` and `scored_trials.jsonl` in the new root.

PERSISTENCE: those two files, then `verify.json` from the second process.

CONSUMER: `verify_later.py` re-reads exactly `pinned_bytes` (33,055,479), checks the pinned SHA-256 and the prefix SHA-256, re-parses, and walks all 1,822 trial rows.

DOWNSTREAM EFFECT: the exact-success rate is lower for the cost-on keep set. That effect is confined to this audit. Production behavior is unchanged by the measurement.

## Causal Chain

This chain is for the claim "cost-driven retention improves later self-edit outcomes."

1. Data enters. `memory/SELF_EDIT.log` holds the result tokens. The scoring pin is the first 33,055,479 bytes, SHA-256 `f859b8ca2f0f84e583a204834d5ced81d70eb0cfee92bb5eec741305c20677b1`. The cost-test prefix remains the first 33,008,379 bytes, SHA-256 `bf05736e4bf7a5a14e5d12f6cf9f3729440fa2d0b329e2ea7bb0dd21d3a89383` (OBSERVED).
2. An observation is created. The pinned file parses to 25,675 matched result records. The prefix parses to 25,624, identical to `full[:25624]` and to the cost index on token and prompt SHA-256 (VERIFIED by `verify_later.py`).
3. A label exists. Exact success is the later token equal to `success`. The contrary signal used to charge the budget was already frozen: a prior formation row with the same prompt key whose token contains `fail` or whose post-result suffix has a non-empty `error:` field. This measurement does not relabel that signal (OBSERVED).
4. A learning update occurs. Absent. The budget is a fixed integer, 100, charged 5 on a paid contrary keep, and it stops paying after 20 charges. No weight, count, or scorer is updated (DISPROVEN as a learning step; already recorded in the cost audit).
5. Updated state persists across a process boundary. The budget traces persist as files. The live server does not load them (OBSERVED).
6. Something else reads that state. This measurement reads the traces. Production code does not (OBSERVED).
7. The read changes a decision. Inside the finished cost test, active mode kept 797 held-out rows and disabled mode kept 1,025. Overlap is 222, only-on is 575, only-off is 803 (VERIFIED by the trace recount).
8. The changed decision changes observable behavior. The two keep sets are different sets of log rows (OBSERVED).
9. The changed behavior has a measurable later consequence. The later exact-success rates differ (VERIFIED).
10. The consequence improves on a criterion independent of the mechanism. It does not. The cost-on exact-success rate is lower (DISPROVEN).

Links 7 through 9 hold inside the experiment for a retention change. Link 4 is absent. Link 10 fails for improvement. The mechanism is not a closed learning loop.

## Adversarial Findings

The simpler account that survives is selection. Rows kept by both arms have the same later outcome: 103 successes out of 113 present tokens, with 81 missing and 28 excluded as charging keys. The cost-on-only rows that clear the charging-key filter contribute 37 successes out of 236 present tokens, and 339 of 575 are missing. The cost-off-only rows contribute 567 successes out of 674 present tokens, with 11 missing and 118 excluded. Adding the pieces recovers the headline: present 113 + 236 = 349 and 113 + 674 = 787; success 103 + 37 = 140 and 103 + 567 = 670; missing 81 + 339 = 420 and 81 + 11 = 92. The cost-on set replaces early repeated contrary keeps that have a later `success` with later refills whose next token is absent or `rejected_meaningless_prompt`.

Checks that were actually run:

- Scoring the charging signal itself as the later outcome. The 4 signal ids are earlier formation rows. `n_skipped_charging_id` and `n_immediate_next_was_charging_signal` are 0 on both arms in `result.json`. The verifier also rejects a later id that is a charging id or that skips an eligible same-key id. No such row was found.
- Treating the 335 refills as charged unlinked rows, or as hidden successes. They are missing. Dropping them does not change the success counts. The cost audit already recorded that the charge never lands on an unlinked row; the 335 changed only because a freed slot reached them.
- Swapping the success definition after seeing the rates. Non-failure is higher, and the histogram shows why. The headline stays exact `success`.
- Shared later tokens double-counting a win. `n_trials_sharing_a_later_id` is 0 in the primary result, and the verifier requires the stored later id to be the next eligible id.
- Tail contamination. The pin contains 51 matched records past the 25,624-row prefix. `n_later_past_prefix` is 0 for both scored arms. None of those 51 records is the next token for a scored keep.
- A keep scoring its own token. The later id is strictly greater than the keep id.
- Truncated prompt keys. The frozen parser is unchanged. Many writers store `prompt[:80]`, so equal SHA-256 can miss a full-prompt link and can inflate `missing`. Both arms use that parser. The 335 refills are the extreme case: no formation key and no later key. This limit was accepted in the cost test and is not repaired here.
- A static heuristic mistaken for learning. The budget math was not reopened. Twenty charges of 5 empty a budget of 100. That is insolvency of a fixed counter.

## Controlled Experiments

No new model run. One comparison, filters locked in `measure_later.py` before the rates were printed.

Population. Holdout rows (`matched id % 5 == 0`) with `decision == keep`, from the frozen active trace (797) and the frozen disabled trace (1,025).

Charging signals. `prior_signal_id` on an active keep with `charged == 5`. Observed: 20 charges, 4 ids, 4 prompt keys. Those rows are formation rows, not holdout keeps.

Primary exclusion. A keep whose `prompt_sha256` equals a charging-signal SHA-256 is excluded. An empty SHA-256 is not a charging key; it stays in the scored set and then counts as missing, because an empty key never links. Cost-on excluded 28 of 797. Cost-off excluded 146 of 1,025. A second exclusion, "the keep row's own id is a charging-signal id," removed 0 in both arms.

Later token. The next record with the same prompt SHA-256 and a strictly greater matched id, skipping ids in the charging-signal id set. That skip did not fire. Each retained row is one trial. Rows are not deduped by key.

Success. Later token equals `success`. Rate denominator equals rows with a later token present. Missing is a separate count. Delta is rate_on minus rate_off, computed with `Decimal`. Direction uses the integer cross-product. "No difference" would require the cross-products to be equal.

335 sensitivity. Cost-on keeps with `formation_key_count == 0` that were drop under the disabled rule and keep under the active rule. The script required the count to be 335 and required those rows to be a subset of the only-on set. All 335 are missing (`n_335_present` 0, `n_335_success` 0, `n_335_nonfailure` 0). After removal, cost-on is 462 input, 434 scored, 85 missing, 349 present, 140 success. Cost-off is unchanged. Direction remains lower.

Source pin. `measure_later.py` took `stat` size, then read that many bytes: 33,055,479. Prefix identity held: 25,624 records, 0 token or SHA-256 mismatches against the cost index, prefix ends on a newline. One unparsed `result:` line is present in the prefix and in the pin, matching the cost test. The measurement did not copy the log and did not write prompt text or prompt hashes into its outputs.

`verify_later.py` does not import `measure_later.py`. It re-reads the pinned byte count, re-parses, recomputes primary success, present, missing, non-failure, and charging-key exclusion for both arms, checks the success direction and the `Decimal` delta, and checks each of the 1,822 trial rows. Exit code 0. `verify.json` records `match: true`, `problems: []`, `checked_trials: 1822`.

Expected before the run: any of higher, lower, or no difference was a complete answer. Observed: lower on exact success.

Limitation. The keep sets are not the same rows, so the rate gap is a property of which rows were retained. The overlap slice shows what the later token does when membership is held fixed. The design does not assign the cost to a single row and then watch that row's next token under both decisions.

## Independent Review

Not required. This mission changed no production code. `feral-independent-review` was not run.

## Evidence Ledger

| Item | Value |
|---|---|
| Experiment root | `memory/experiments/later_outcome_after_cost_20261019/` |
| Cost root, read-only | `memory/experiments/outcome_signal_cost_20261019/` |
| Pinned log bytes / SHA-256 | 33055479 / `f859b8ca2f0f84e583a204834d5ced81d70eb0cfee92bb5eec741305c20677b1` |
| Prefix bytes / SHA-256 | 33008379 / `bf05736e4bf7a5a14e5d12f6cf9f3729440fa2d0b329e2ea7bb0dd21d3a89383` |
| Matched records, prefix / pin | 25624 / 25675 |
| Records past the prefix | 51, of which 0 are a scored keep's next token |
| Charges / signal ids / signal keys | 20 / 4 / 4 |
| Cost-on input, excluded key, scored, missing, present, success, non-failure | 797, 28, 769, 420, 349, 140, 327 |
| Cost-off input, excluded key, scored, missing, present, success, non-failure | 1025, 146, 879, 92, 787, 670, 671 |
| Exact-success rates | 140/349 = 0.4011461318051575931232091691; 670/787 = 0.8513341804320203303684879288 |
| Exact-success delta and direction | -0.4501880486268627372452787597; lower |
| Non-failure rates | 327/349 = 0.9369627507163323782234957020; 671/787 = 0.8526048284625158831003811944 |
| Non-failure delta and direction | +0.0843579222538164951231145076; higher |
| Fail-or-error counts | cost-on 22 (12 load_failed + 10 staging_import_failed); cost-off 116 (116 load_failed) |
| 335 refills | 335 missing, 0 present; success delta unchanged |
| Overlap / only-on / only-off success | 103/113; 37/236; 567/674 |
| Verifier | `match: true`, 1822 trials, exit 0 |
| `measure_later.py` | 22051 bytes, SHA-256 `b6a717f0dc3466d83ee0030fc0d79d8c99b9f40a9cfd9bd51c29d7f843b53323` |
| `verify_later.py` | 8549 bytes, SHA-256 `b3fede785468237d9ba5c57750616f0cdcaf838d8b4db8a4a19a5c115084b1ca` |
| `result.json` | 10191 bytes, SHA-256 `e5b0944e2328389aff7eaad70852d209c9a9c0c6c41ddf49380f907ab513ad6d` |
| `scored_trials.jsonl` | 602826 bytes, 1822 lines, SHA-256 `bdf01f468d056f244e6ba2941f68d17c5a87d7a9939651071e746355455a3556` |
| `verify.json` | 256 bytes, SHA-256 `b55a91daace45da367c968f5687220a82461218e4e92c81cf97aae01f999293d` |

## Final Classification

The outcome-signal budget, as a mechanism, remains a root-local static integer policy. Production consumption of that policy is L0: the live server does not read it. Inside the experiment, links 7 through 9 show a retention change with a measurable later-token difference. Link 10 improvement on exact `success` is false, so the mechanism does not reach L3. It is not Level 4. This measurement does not move that classification.

## What Is Actually Proven

- On the precommitted filters, the cost-on later exact-success rate is lower than the cost-off rate: 140/349 versus 670/787, delta -0.4501880486268627372452787597 (VERIFIED).
- 420 cost-on scored rows and 92 cost-off scored rows have no later token. They are missing, and they are not in the rates (VERIFIED).
- The 335 no-formation-key refills are all missing. Excluding them leaves the same success counts and the same lower direction (VERIFIED).
- The non-failure rate is higher for cost-on because `rejected_meaningless_prompt` is counted as non-failure. That is a different definition, and it is not the headline (VERIFIED).
- Where both arms keep the same row, the later success count is the same, 103/113. The gap is the changed membership: only-on 37/236 and only-off 567/674 (VERIFIED).
- The cost-root artifacts and the closed-branch files listed below still have the hashes recorded before this measurement (OBSERVED).

## What Is Only Supported

- The recorded gap is selection among different retained rows, which is the account the partition supports. That is the tested simpler explanation of the rate difference (SUPPORTED). It does not identify a causal effect of the charge itself.
- The first script's row-skip sensitivity is also lower on exact success (165/376 versus 802/932). `verify_later.py` did not recompute that sensitivity (OBSERVED as a first-script output; the qualitative agreement is SUPPORTED only as far as that file).

## What Remains Unknown

- Whether the cost, as a cause, made later edits worse. The keep sets differ, so the rate comparison is not a paired outcome on one decision (UNKNOWN).
- How many empty later-token results are true absences, and how many are prompt-truncation misses under the frozen parser (UNKNOWN). The parser was not repaired.
- Whether any other success definition, chosen after these rates, would reverse the headline. That question was not tested, and it is out of scope. The precommitted secondary definition already moves the other way and was not adopted as the headline.

## What Was Disproven

The claim that this retention shift improves later outcomes, on the exact-success rate the ceiling note named, is disproven. The ceiling note's required comparison was: measure the later self-edit result token on the same prompt key after the retention decision, and compare that rate for the cost-on keep set versus the cost-off keep set, on rows that were not the contrary signal used to charge the budget. That comparison was run. The cost-on rate is lower.

The claim that dropping the 335 refills removes the difference is disproven. They contribute no present trials and no successes.

The claim that the secondary non-failure increase is the outcome result is disproven as a reading of this mission. Non-failure was precommitted as a separate report, and exact `success` decides the direction.

## Recommendations

Stop. Do not promote the cost rule, do not retune the budget, and do not chain another test. A lower later-success rate is a complete outcome for the question that was asked. The static integer policy is unchanged.

## Integrity Record

Pre-measurement clock for the log pin: 2026-10-19T21:38:04Z. Pre-audit confirmation clock: 2026-10-19T21:45:38Z. Git HEAD at both clocks: `4d2932c5f9a74e46ac866862ac4972b0787d7b8f`.

Closed-branch and finished-audit hashes at 21:45:38Z, unchanged from the 21:38:04Z record:

| Path | Bytes | SHA-256 |
|---|---:|---|
| `app/experiments/persistent_routing/selector.py` | 5149 | `71f6f04fa522c78c49ea8eddeb67373335d8f6ea6b574c29220f0379fe0c6127` |
| `memory/experiments/persistent_routing/log_E_experience.jsonl` | 5486 | `4f5bb2377035a3ce94a1c21df6aa83e7f000e45a44e32eb296b01fa4968f0241` |
| `memory/experiments/strategy_characterization/stage1/log_stage1.jsonl` | 165572 | `7f9d9533cc05add8171eae632f3c9be7678233c2424ef7810858a64e1b4f826a` |
| `memory/experiments/richer_experience_20261019/log_E_experience_rich.jsonl` | 76571 | `547f17b3da8aecfa2b0e1dbeeba36db23990cf9f0dc0e6181e7e60e33aa7f7be` |
| `audits/2026-10-19_richer_experience_capture.md` | 10612 | `1b66ed539fb856bc6c33bbccbebe776369d55b730d37ea88b6ae2131d81ac71f` |
| `audits/2026-10-19_self_edit_token_visibility.md` | 13323 | `e82d5668780bc5897edb73ed32722999bdccd0e1315c2a42d769aba7c3c5d722` |
| `audits/2026-10-19_memory_consolidation_outcome_signal.md` | 12813 | `bf1cc7ef6b39dbbe3f85ced18eb8304425e1ab36f3106b92e92adddb54e8c921` |
| `audits/2026-10-19_outcome_signal_relay_comparison.md` | 11078 | `f7e5b8d7351c716f44b95b74e02e988b33ed9cfa05aa6d9d677ca8bc4124fbfc` |
| `audits/2026-10-19_outcome_signal_cost_retention.md` | 23651 | `00e7c5a61c94464e9479be5201d66dee49586e370949351b18309633916f13e8` |
| `audits/2026-10-19_outcome_signal_cost_ceiling.md` | 19824 | `6cf64b91ff5350c409bef198a687d33bd08969ba0fd80a418953feeb79843d9f` |
| `app/core/echo_model_orchestrator.py` | 90538 | `6dcc8b90a33008e889821f1e41058cd6291fca754ee6418fb30444a0e99b0720` |
| `app/core/river_deliberation.py` | 81478 | `c7d68f6e09458007f230bb00138738c1115a70fc919aab1fb3717220724370cc` |
| `grok_relay/from_m5.md` | 12054 | `d3fe00fc485068d01f95dfe1615d4d8405d18f7fc96fbe3915af89662338f93c` |
| `grok_relay/.outbox.jsonl` | 548 | `c1f5102d99f8fc29bc5ee204154edc14e0439509bdd904a653f8e6a5b0cad17d` |
| `grok_relay/.last_seen_from_ark.json` | 91 | `8dddc033cd5869a0007cc711bd771124ae9303a2e15d392631f16272b15b882f` |
| `grok_relay/.inbox_from_ark.md` | 3871 | `10b5363bac7f675b720b242a744a3b6bd765be2f863e7625286fa73efe9ae3c4` |

Frozen cost root, unchanged:

| Path | Bytes | SHA-256 |
|---|---:|---|
| `result.json` | 1796 | `c2174b9b8bfa38647a0954c949632ffcbc8510a74d35a1e7dad572dc45762983` |
| `index.jsonl` | 7666840 | `2f6ed01a125d5951cd61ae95004c68cd53fdfdc07e46c1cb476f2a64d97e3d58` |
| `budget_trace_active.jsonl` | 1109023 | `bd9d369fc9915213001842fcbee0f844aa477bf35c98dcdac545c3dc104f7cd9` |
| `budget_trace_disabled.jsonl` | 1112823 | `5c8041c1aa500d08eee32017ead8e03242edf07a10e0ea8a477afe7095a4ec2b` |
| `status.txt` | 91 | `339cd4cbfca37fa12e94e6096b27dd78994e5df59c652fc4bde08313eadd532d` |
| `run_cost.py` | 18564 | `c0aab29d991679b2915722dbcb6ccd46475910a25e087aba353a7ae7a3d31b18` |

Live files at 21:45:38Z. These moved relative to the 21:38:04Z pin because the server was already running. This measurement read `SELF_EDIT.log` and did not write it. The prefix of 33,008,379 bytes was rechecked at 21:45:38Z and still hashes to `bf05736e4bf7a5a14e5d12f6cf9f3729440fa2d0b329e2ea7bb0dd21d3a89383`.

| Path | Bytes at 21:38:04Z | SHA-256 at 21:38:04Z | Bytes at 21:45:38Z | SHA-256 at 21:45:38Z |
|---|---:|---|---:|---|
| `memory/SELF_EDIT.log` | 33055479 | `f859b8ca2f0f84e583a204834d5ced81d70eb0cfee92bb5eec741305c20677b1` | 33055738 | `fa2e88ca431fc82ca1ba0d804d9193a4c8e04f93f586f0702f9f2865d1c3fd9e` |
| `memory/memory_meta.json` | 121508176 | `6e31460e1b18bf0d41584304f4744b42811753872e40c23ce0e2ccfbac4bc6b6` | 121510281 | `c33b5439a051f179eab03156bcd234e3577509e7ee7931f0b5d5ed34669ad5ec` |
| `memory/faiss.index` | 222228525 | `6ae7af525dc21b238d806fdecd5e173c52d5f9770921c6dcd844c80b2c683dc1` | 222230061 | `6a24e2905593fc99a4695fa2f7f797822c22bf12da9e7f4001180b4b9b8ecf10` |
| `memory/consolidation_log.jsonl` | 456936 | `8031bacfb2e06a236517fc3375d2909b6453d09987b4f8bbcc7ca2f4d5413b3f` | 456936 | `8031bacfb2e06a236517fc3375d2909b6453d09987b4f8bbcc7ca2f4d5413b3f` |
| `memory/self_model.json` | 19492 | `1618de0e584d2b548a4888f1ff5f0344e05cfd0f4bd4868137eb22890cc0b330` | 19490 | `5dc622dadb8d72f13535973cf792827c0aa41c86bd4af6cf4856164ac03f1cf5` |
| `memory/memory_journal_active.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

Post-audit rehash at 2026-10-19T21:48:47Z. Git HEAD is still `4d2932c5f9a74e46ac866862ac4972b0787d7b8f`. Every closed-branch path in the table above, every finished audit in that table, and every frozen cost-root file still has the same size and SHA-256. The cost-test prefix and the measurement pin still match inside the grown log: the first 33,008,379 bytes hash to `bf05736e4bf7a5a14e5d12f6cf9f3729440fa2d0b329e2ea7bb0dd21d3a89383`, and the first 33,055,479 bytes hash to `f859b8ca2f0f84e583a204834d5ced81d70eb0cfee92bb5eec741305c20677b1`. Live files that moved again after 21:45:38Z, by the already-running server: `memory/SELF_EDIT.log` 33055963 bytes, SHA-256 `9a4e5af1700baa570afcee9881d99ef714396cb78f3bffd38a30f06ad84ce610`; `memory/memory_meta.json` 121512846 bytes, SHA-256 `64b15ecedc6d84105944f753a52e22863810e7101dae8312adebb2d26a656b61`; `memory/faiss.index` 222231597 bytes, SHA-256 `5494d837c914240a3c23762c1fce4c268a8a693e7e631facf22deca259bc3a15`; `memory/self_model.json` 19492 bytes, SHA-256 `563d9f11b97f29f9c7ee0ad201c36f35cef4b548ab072ebf4c21ee99b7d4445e`. `memory/consolidation_log.jsonl` and `memory/memory_journal_active.log` are unchanged from the 21:45:38Z row. Experiment-root hashes are unchanged from the evidence ledger.

production changes: NO
files changed: `memory/experiments/later_outcome_after_cost_20261019/measure_later.py`, `verify_later.py`, `result.json`, `scored_trials.jsonl`, `verify.json`; this audit
Git HEAD before: `4d2932c5f9a74e46ac866862ac4972b0787d7b8f`
Git HEAD after: `4d2932c5f9a74e46ac866862ac4972b0787d7b8f`
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: short-lived `python3` measurement and hash processes, all exited
configuration changes: NO
test changes: NO
temporary files created: none outside the experiment root and this audit
temporary files cleaned: YES
orphaned processes: none from this measurement
known anomalies: live-server drift of `SELF_EDIT.log`, `memory_meta.json`, `faiss.index`, and `self_model.json` between 21:38:04Z and 21:45:38Z; consolidation log and the active journal did not move; the cost-test prefix hash held
known deviations from requested methodology: none. The row-skip sensitivity was left as a first-script output and was not given a second parse. The headline rates, the 335 missing count, and the keep-set partition were recomputed.
