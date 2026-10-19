# Outcome-Signal Cost Test, then Conditional Ceiling Note

**Date:** 2026-10-19
**Type:** Report of one already-run isolated experiment, plus a conditional ceiling note. No new run.

## Executive Verdict

Held-out retention decisions changed when a root-local budget charged 5 for each keep that ignored an available prior FAIL or error token (VERIFIED). The shift is insolvency of a fixed integer budget after 20 paid keeps, not a learned policy (VERIFIED on the trace; learning DISPROVEN). Recorded spend is 100 with the cost on and 0 with it off. The only reduction is against the counterfactual bill of the cost-off keep set, 4115. Because at least one decision changed, the ceiling note below is included. Outcome improvement was not measured (UNKNOWN).

## Question

On a held-out slice of existing self-edit records, does a pre-specified persistent cost of 5, drawn from a budget that starts at 100, change any keep/drop decision relative to the same retention rule with the cost disabled? If it does, what ceiling does that result imply, and what single further measurement would be required before calling the change an improvement?

## Hypotheses

- H0: no held-out keep/drop decision differs. DISPROVEN. 803 keeps became drops and 575 drops became keeps.
- H1: the cost-on pass shifts decisions so as to avoid an unpaid contrary keep, by the rule frozen before the comparison. VERIFIED for this slice. `showed_shift_to_avoid_cost` is true. The mechanism that produces it is budget exhaustion, not an update step.

## Scope / Non-Goals

This file reports the experiment already stored at `memory/experiments/outcome_signal_cost_20261019/`. That run is not repeated here. No second experiment root was created. `run_cost.py` was not edited. The earlier audit `audits/2026-10-19_outcome_signal_cost_retention.md` was not edited.

Production memory, FAISS, consolidation, selectors, and governance files were not written. No model output was generated. No package was installed. The strategy-routing, richer-experience-tail, and self-edit-token-visibility branches were not reopened. No relay note was sent. The named outcome measurement in the ceiling note was not executed. The budget was not promoted into any selector.

Non-template, in this corpus, means `formation_key_count == 0`: the holdout prompt key is absent from the formation index. This log is `memory/SELF_EDIT.log`. It is not the six Stage-1 templates. A later same-key result token is the measurement that would be required to talk about outcome improvement. A count of prior FAIL tokens inside the kept set is the charge rule itself and is not that measurement.

## Evidence Summary

| Claim | Label | Source | Justification |
|---|---|---|---|
| Prefix of 33008379 bytes still hashes to the frozen digest | VERIFIED | `sha256` of that prefix, 2026-10-19T21:23:44Z | Matches `result.json` `source_sha256` |
| 5125 holdout rows, slots 1025, budget 100, cost 5 | OBSERVED | `result.json` and index header | Re-read this session |
| 803 keep-to-drop, all contrary, budget already under 5 | VERIFIED | both budget traces, recounted | 0 of those 803 have `formation_key_count == 0` |
| 575 drop-to-keep, none contrary | VERIFIED | both budget traces, recounted | 335 of them have `formation_key_count == 0` |
| Active budget ends at 0 after exactly 20 charges of 5 | VERIFIED | `budget_trace_active.jsonl` | Charge ids listed below |
| Disabled budget stays 100 and charges 0 | VERIFIED | `budget_trace_disabled.jsonl` | Every row |
| Recorded spend 100 is greater than recorded spend 0 | VERIFIED | `result.json` flags | `recorded_active_spend_lt_disabled` is false |
| 100 is less than the counterfactual 4115 | VERIFIED | 5 times 823 contrary keeps when disabled | `active_spend_lt_counterfactual` is true |
| Production does not read this budget | SUPPORTED | mission scope and prior cost audit; this session did not re-audit every reader | No production file was a write target |
| The shift improves later self-edit outcomes | UNKNOWN | not measured | Ceiling note names the missing measurement |

## Repository Archaeology

The cost root already existed. This session only read it.

| Path | Bytes | SHA-256 |
|---|---:|---|
| `memory/experiments/outcome_signal_cost_20261019/run_cost.py` | 18564 | `c0aab29d991679b2915722dbcb6ccd46475910a25e087aba353a7ae7a3d31b18` |
| `memory/experiments/outcome_signal_cost_20261019/result.json` | 1796 | `c2174b9b8bfa38647a0954c949632ffcbc8510a74d35a1e7dad572dc45762983` |
| `memory/experiments/outcome_signal_cost_20261019/index.jsonl` | 7666840 | `2f6ed01a125d5951cd61ae95004c68cd53fdfdc07e46c1cb476f2a64d97e3d58` |
| `memory/experiments/outcome_signal_cost_20261019/budget_trace_active.jsonl` | 1109023 | `bd9d369fc9915213001842fcbee0f844aa477bf35c98dcdac545c3dc104f7cd9` |
| `memory/experiments/outcome_signal_cost_20261019/budget_trace_disabled.jsonl` | 1112823 | `5c8041c1aa500d08eee32017ead8e03242edf07a10e0ea8a477afe7095a4ec2b` |
| `memory/experiments/outcome_signal_cost_20261019/status.txt` | 91 | `339cd4cbfca37fa12e94e6096b27dd78994e5df59c652fc4bde08313eadd532d` |

Trace digests match the fields inside `result.json`. Status text is `unit_checks_passed`, `prefix_ok`, and `done differ=True avoid=True drop=803 keep=575 budget_active=0`. Index rows store id, split, token, fail and error flags, prompt hash, formation counts, contrary, prior signal id, and kind. They do not store line text.

## Runtime Trace

TRIGGER: a holdout row whose matched id is divisible by 5, walked in ascending id order. SIGNAL: a formation row with a smaller id, the same normalized prompt hash, and either a result token containing `fail` or a non-empty `error:` field after the result span. GATE: if slots remain and the row is contrary and the budget is below 5, drop it, do not consume a slot, and do not charge. Otherwise keep, consume one slot, and if the cost is on and the row is contrary, subtract 5. DOWNSTREAM EFFECT: the later holdout row sees the reduced budget or the freed slot. Production selectors are outside this chain.

## Causal Chain

1. Data enters: existing `SELF_EDIT.log` lines inside the frozen prefix. OBSERVED.
2. Observation: parsed `result:` token and post-result `error:` field. OBSERVED in the index.
3. Label: contrary is a deterministic read of an earlier formation row. It is not a new reward and it is not the candidate's own token. OBSERVED.
4. Learning update: none. The budget rule was fixed before the holdout pass. DISPROVEN as learning.
5. Persistence across the pass: the integer budget is carried from decision to decision and written to the trace. OBSERVED. It is not loaded by the running server.
6. Later read: the next decision in the same pass reads that integer. OBSERVED.
7. Decision change: 1378 holdout rows differ. VERIFIED.
8. Observable behavior: keep counts 1025 versus 797, and 228 slots left unused when the cost is on. VERIFIED.
9. Measurable consequence inside the slice: contrary keeps fall from 823 to 20, and the active budget ends at 0. VERIFIED.
10. Improvement on a criterion independent of the charge: not measured. UNKNOWN. Recorded spend rises from 0 to 100, so "learned to spend less" is DISPROVEN on the recorded ledger. It is true only against the counterfactual 4115.

## Adversarial Findings

The unit checks inside `run_cost.py` show the rule can differ on toy rows. Those checks are not the experimental result. The result is the 5125-row replay.

Own-token confound: a holdout row is never its own prior signal, and a holdout row is never a signal for a later holdout row. Formation rows are the only signal source.

Unlinked items: 335 decision changes have `formation_key_count == 0`. All 335 are drop-to-keep. Keep-to-drop on unlinked rows is 0. Keep-to-drop on non-contrary rows is 0. The cost was not charged on those rows. They changed because a refused contrary keep left a slot that a later non-contrary row filled. That is slot refill under the frozen rule. It does not falsify the charge gate. It does falsify any reading that says the cost touched only rows that carried a prior signal.

Same keep count: false. Active keeps 797. Disabled keeps 1025. Unused active slots at the end of the trace: 228.

Static heuristic dressed as learning: the rule does not fit a scorer, does not update from the holdout outcome, and stops paying once 100/5 is exhausted. Calling that adaptation is DISPROVEN.

## Controlled Experiments

No new comparison was run for this audit. The comparison below is the one already stored in the cost root. It was prospective: the rule, the split, the slot count, and the avoidance flags were fixed before the holdout outcomes were used.

Source: the first 33008379 bytes of `memory/SELF_EDIT.log`. SHA-256 `bf05736e4bf7a5a14e5d12f6cf9f3729440fa2d0b329e2ea7bb0dd21d3a89383`. Reconfirmed on the live file at 2026-10-19T21:23:44Z. The live file was already longer than the prefix. The tail was not scored.

Identity, from `result.json`: 170729 lines in the prefix, 25624 matched records, 20499 formation, 5125 holdout (`matched id % 5 == 0`). Slots = `max(1, int(5125 * 0.2))` = 1025. Contrary holdout rows: 4348. Holdout rows with `formation_key_count == 0`: 409. Holdout rows whose prompt key also appears in formation: 4709.

Exact cost rule, same in both passes except the charge:

- Walk holdout rows in ascending matched id. Priority is that order. File-order slot fill.
- If no slots remain, drop.
- If the cost is disabled, keep whenever a slot remains. Budget stays 100. Charge stays 0.
- If the cost is active, the row is contrary, and the budget is below 5, drop. Do not consume a slot. Do not charge a partial amount.
- If the cost is active, the row is contrary, and the budget is at least 5, keep, consume one slot, and subtract 5.
- If the row is not contrary, keep and consume one slot. Do not charge.
- The budget is an integer, starts at 100, and is not allowed to go negative.

Budget trace, cost active. Twenty charges of 5, then refusals:

| After charge | seq | id | budget after |
|---:|---:|---:|---:|
| 1 | 5 | 25 | 95 |
| 2 | 6 | 30 | 90 |
| 3 | 7 | 35 | 85 |
| 4 | 9 | 45 | 80 |
| 5 | 10 | 50 | 75 |
| 6 | 17 | 85 | 70 |
| 7 | 21 | 105 | 65 |
| 8 | 22 | 110 | 60 |
| 9 | 23 | 115 | 55 |
| 10 | 24 | 120 | 50 |
| 11 | 25 | 125 | 45 |
| 12 | 26 | 130 | 40 |
| 13 | 27 | 135 | 35 |
| 14 | 30 | 150 | 30 |
| 15 | 31 | 155 | 25 |
| 16 | 32 | 160 | 20 |
| 17 | 33 | 165 | 15 |
| 18 | 34 | 170 | 10 |
| 19 | 35 | 175 | 5 |
| 20 | 36 | 180 | 0 |

The first refusal is seq 37, id 185, budget before the decision 0, charged 0, slots unchanged (988 to 988). Index rows for holdout ids 185, 190, and 195 are contrary, token `success`, and share one prompt hash with formation id 18. Formation id 18 is earlier, token `load_failed`, `is_fail` true, `has_error` true.

Disabled trace: 5125 decisions, budget 100 before and after every row, charge 0 on every row, 1025 keeps, 0 slots left.

Prospective results:

| Quantity | Cost disabled | Cost active |
|---|---:|---:|
| Keeps | 1025 | 797 |
| Drops | 4100 | 4328 |
| Final budget | 100 | 0 |
| Recorded spend | 0 | 100 |
| Contrary keeps | 823 | 20 |
| Decisions changed, keep to drop | 803 | all contrary |
| Decisions changed, drop to keep | 575 | none contrary |
| Changes with `formation_key_count == 0` | 335 | all drop to keep |

Decision changes: 1378. Budget delta on the recorded ledger: active ends 100 below disabled. Counterfactual charge if every disabled contrary keep had been billed: 5 * 823 = 4115. Active spend is lower than that counterfactual and higher than the disabled recorded spend.

Drop-to-keep partition, mutually exclusive, sums to 575:

- 335 with `formation_key_count == 0`
- 24 with a formation key and `formation_prior_count == 0`
- 215 with `formation_key_count > 1`, at least one earlier formation row, and no contrary signal
- 1 with `formation_key_count == 1`, exactly one earlier formation row, and no contrary signal

Changes on non-template items occurred. They are the 335 unlinked drop-to-keep rows. None of the 803 keep-to-drop rows are non-template.

## Independent Review

Not required. This mission did not change production code. `feral-independent-review` was not run.

## Evidence Ledger

Primary record: `memory/experiments/outcome_signal_cost_20261019/result.json`, plus the two trace files and `index.jsonl` hashed above. This session's recount of both traces matched those fields: 20 charges, budgets 95 down to 0, first refusal id 185, keeps 797 and 1025, contrary keeps 20 and 823, keep-to-drop 803, drop-to-keep 575.

## Final Classification

The mechanism is a static integer policy inside one experiment root. Links 7 through 9 hold for that pre-specified counter. Link 4 does not. Link 10 does not hold for recorded spend, and it was not tested for later result tokens. This is not L2 learning, not L3, and not Level 4. Production consumption of the budget is L0: the running server does not read it.

## What Is Actually Proven

On this frozen prefix and this holdout rule, enabling the cost changes retention. After 20 charges the budget is 0, later contrary candidates are dropped without taking a slot, and 575 later non-contrary candidates are kept in slots the disabled pass had already filled. Every direct keep-to-drop row had a contrary formation prior. The active pass keeps fewer rows overall (797 versus 1025).

## What Is Only Supported

The same arithmetic would appear on any walk with more than 20 contrary rows inside the disabled keep window and enough later non-contrary rows to refill some freed slots. That is a property of this rule and this order, read off the trace, not a second dataset.

## What Remains Unknown

Whether the cost-on keep set has a better later `result:` token, on the same prompt key, than the cost-off keep set. The rows used as the contrary charge must be excluded from that comparison. That measurement was not run.

## What Was Disproven

H0, no decision change, is false on this slice. "The cost pass spends less than the disabled pass" is false on the recorded ledger (100 versus 0). "The cost is a learned scorer" is false: nothing was fit, and payment stops because 100 is divisible by 5 twenty times. "No unlinked decision changed" is false: 335 unlinked rows moved from drop to keep by slot refill.

## Ceiling Note

After twenty charges of 5 emptied a budget of 100, later held-out keep/drop choices changed. The highest learning or self-knowledge behavior this result makes testable, with existing logs, no new hardware, no external model, and no gate change, is a pre-specified persistent counter that reads an existing FAIL or error token and alters a later retention choice. To claim that change improves outcomes rather than only altering retention, measure the later self-edit result token on the same prompt key after the retention decision, and compare that rate for the cost-on keep set versus the cost-off keep set, on rows that were not the contrary signal used to charge the budget.

## Recommendations

Stop. Do not promote the budget. Do not run the measurement named in the ceiling note under this authorization. Do not add another experiment root.

## Integrity Record

production changes: NO
files changed: `audits/2026-10-19_outcome_signal_cost_ceiling.md` only. The cost root and `audits/2026-10-19_outcome_signal_cost_retention.md` were read and not written.
Git HEAD before: `4d2932c5f9a74e46ac866862ac4972b0787d7b8f`
Git HEAD after: `4d2932c5f9a74e46ac866862ac4972b0787d7b8f` (unchanged at 2026-10-19T21:26:26Z)
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: read-only `python3` hash and trace recounts, all exited
configuration changes: NO
test changes: NO
temporary files created: none
temporary files cleaned: YES
orphaned processes: none started
known anomalies: the live server continued to append production artifacts while this audit was written. Those writes are not this mission's. The scored prefix hash did not change.
known deviations from requested methodology: Part 1 was not re-run. The prospective comparison already existed, and this mission's stop rule forbids a second root and a retune. The ceiling note was added because the stored result shows decision changes.

Closed-branch and governance hashes at 2026-10-19T21:23:44Z, all matching the previously recorded values:

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
| `app/core/echo_model_orchestrator.py` | 90538 | `6dcc8b90a33008e889821f1e41058cd6291fca754ee6418fb30444a0e99b0720` |
| `app/core/river_deliberation.py` | 81478 | `c7d68f6e09458007f230bb00138738c1115a70fc919aab1fb3717220724370cc` |
| `grok_relay/from_m5.md` | 12054 | `d3fe00fc485068d01f95dfe1615d4d8405d18f7fc96fbe3915af89662338f93c` |
| `grok_relay/.outbox.jsonl` | 548 | `c1f5102d99f8fc29bc5ee204154edc14e0439509bdd904a653f8e6a5b0cad17d` |
| `grok_relay/.last_seen_from_ark.json` | 91 | `8dddc033cd5869a0007cc711bd771124ae9303a2e15d392631f16272b15b882f` |
| `grok_relay/.inbox_from_ark.md` | 3871 | `10b5363bac7f675b720b242a744a3b6bd765be2f863e7625286fa73efe9ae3c4` |

Live production artifacts at the same clock, scored prefix unchanged, live files larger than the cost-run boundary. Not written by this mission:

| Path | Bytes now | SHA-256 now |
|---|---:|---|
| `memory/SELF_EDIT.log` | 33052772 | `d6c383927bb546e6d3ab93d6b83884e302e569a2807ecfb267e34c4727bc0016` |
| `memory/memory_meta.json` | 121502115 | `6726306c70aa18a3197b5569c060cb2881dbe75b1c06eef17108d15c761b04e1` |
| `memory/faiss.index` | 222225453 | `cbedcf71f79a6f594b83cff8cf0d93b062c4f5cc79d1ca46a678d33d4c7a28e9` |
| `memory/consolidation_log.jsonl` | 456779 | `d0faba13b038ed02ae586c5a71f04b97ed6156f66413e44db64635f5b5902684` |
| `memory/self_model.json` | 19491 | `29a8b33db7762e58c3a8248a140f1d7917a2b52f282326f04a6ee8449e1f3be3` |
| `memory/memory_journal_active.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The frozen prefix inside `memory/SELF_EDIT.log` is still `bf05736e4bf7a5a14e5d12f6cf9f3729440fa2d0b329e2ea7bb0dd21d3a89383`.

Post-write recheck at 2026-10-19T21:26:26Z: closed-branch hashes above were unchanged, and `SELF_EDIT.log`, `memory_meta.json`, `faiss.index`, and `memory_journal_active.log` still matched the live table. Two live files moved again during the write, still not written by this mission: `memory/consolidation_log.jsonl` 456936 bytes, SHA-256 `8031bacfb2e06a236517fc3375d2909b6453d09987b4f8bbcc7ca2f4d5413b3f`; `memory/self_model.json` 19549 bytes, SHA-256 `0934ad9f8e13d7e0a0ae532829535378ca1604ac55febd59419480162fadc024`.
