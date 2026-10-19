# Outcome-Signal Cost on Retention Budget

**Date:** 2026-10-19
**Type:** Investigation + bounded experiment

## Executive Verdict

On the frozen `SELF_EDIT.log` prefix, a root-local retention budget of 100 that charges 5 for keeping a held-out row despite an available prior contrary signal kept a different set than the same slot rule with the charge disabled (VERIFIED). The active pass paid for 20 contrary keeps, reached 0, and then dropped 803 further contrary rows the disabled pass had kept. It also kept 575 later rows the disabled pass had dropped, 335 of them with no formation prompt link. Recorded spend was 100 with the cost on and 0 with the cost off. Spend fell only relative to the uncapped bill for the disabled contrary keep set, which is 4115. The shift is exhaustion of a fixed integer after 20 payments. It is a static rule inside one experiment root. Production retention did not read it.

## Question

When a retention decision keeps an item that already has a prior FAIL or error signal in a root-local index, and that keep decrements a persistent budget, do later retention choices on a held-out slice change so that less of that budget is spent?

## Hypotheses

- **H1.** At least one held-out keep/drop differs. Every row kept with the cost off and dropped with the cost on is contrary. The active pass keeps fewer contrary rows than the disabled pass.
- **H0.** The keep/drop set is identical under both conditions. The cost may still be paid.

H1 is the outcome the precommitted flags record. `decisions_differ` is true. `showed_shift_to_avoid_cost` is true. H0 is not what this slice did. The mechanism that produced H1 was fixed before the run: after 20 paid contrary keeps the budget is 0, and a later contrary keep is refused. With 823 contrary rows inside the disabled keep set, that refusal was arithmetically due once the count exceeded 20. The held-out slice could have returned H0 if that count had been 20 or fewer. It was 823.

## Scope / Non-Goals

This mission created one experiment root, `memory/experiments/outcome_signal_cost_20261019/`, and this audit. It scored the first 33008379 bytes of `memory/SELF_EDIT.log` only. It did not generate model output, install packages, start services, edit production memory, FAISS, consolidation, the closed selector, richer-experience logs, or governance files, send a relay note, or touch the Ark. It did not promote the budget. The stop rule forbids a follow-on test.

"Non-template" in this audit means `formation_key_count == 0`: the normalized prompt key is absent from the formation index. This corpus is `SELF_EDIT.log`. It is not the six Stage-1 task templates.

## Evidence Summary

| Claim | Label | Source | Justification |
|---|---|---|---|
| Scored prefix is 33008379 bytes, SHA-256 `bf05736e4bf7a5a14e5d12f6cf9f3729440fa2d0b329e2ea7bb0dd21d3a89383` | VERIFIED | `run_cost.py` exit 0; second process `hashlib.sha256` | Both reads matched the frozen digest before any comparison. |
| 25624 matched rows, 1 unparsed `result:` line, holdout 5125, formation 20499, token histograms match the prior test | VERIFIED | Script identity gate; independent `Counter` recount | Recount matched `EXPECTED_MATCHED` and `EXPECTED_HOLDOUT` exactly. |
| Active and disabled traces obey the frozen arithmetic | VERIFIED | Second process over both JSONL traces | 20 charges of 5, budgets 100→0 and 100→100, no keep at 0 slots, every keep→drop had `budget_before < 5`. |
| Three sampled links are real prior `load_failed` rows | VERIFIED | Second process re-parse of the prefix | Ids 185, 190, 195 share a prompt hash with formation id 18; id 18 is smaller, `load_failed`, and has an `error:` suffix. |
| 335 decision changes are unlinked | VERIFIED | Trace fields `formation_key_count` | All 335 are drop→keep. Keep→drop on unlinked rows is 0. |
| Production artifacts and closed-branch hashes are unchanged by this process | VERIFIED | `shasum -a 256` before and after; `git rev-parse HEAD` | HEAD stayed `4d2932c5f9a74e46ac866862ac4972b0787d7b8f`. Closed-branch digests matched. Live-server drift is separate below. |
| The shift is a learned retention policy | DISPROVEN | Frozen rule in `run_cost.py`; trace of 20 fixed charges | No update step. The same function runs both passes. Only `enabled` differs. |

## Repository Archaeology

| Fact | Result |
|---|---|
| Exists | `memory/experiments/outcome_signal_cost_20261019/run_cost.py` and its outputs exist only under that root, plus this audit. |
| Imported | The script imports `hashlib`, `json`, `re`, `sys`, `pathlib`. It does not import application modules. |
| Reachable from production | No production file imports this root. |
| Executed | `python3 memory/experiments/outcome_signal_cost_20261019/run_cost.py` exited 0. Status file: `unit_checks_passed`, `prefix_ok`, `done differ=True avoid=True drop=803 keep=575 budget_active=0`. |
| Produces state | Root-local `index.jsonl`, `budget_trace_active.jsonl`, `budget_trace_disabled.jsonl`, `result.json`, `status.txt`. |
| Consumed by production | No production reader of these files was added. |
| Behaviorally consequential in production | No. The keep/drop difference exists only in the two traces. |

The signal source is the same journal surface named in `audits/2026-10-19_memory_consolidation_outcome_signal.md`: `append_to_journal("SELF_EDIT", ...)` writes `memory/SELF_EDIT.log`. Production prune, FAISS meta, and prompt assembly do not read the `result:` token. This experiment does not change that.

## Runtime Trace

TRIGGER: read exactly 33008379 bytes from `memory/SELF_EDIT.log` → hash check against the frozen digest → parse the first `result:` token on each line → holdout if matched id % 5 == 0.

SIGNAL: formation rows only (id % 5 != 0). A holdout row is contrary when an earlier formation row has the same SHA-256 of the normalized `prompt:` text and that earlier row's token contains `fail` or its post-result suffix contains a non-empty `error:` field. Empty prompt keys do not link. A holdout row is not a signal for a later holdout row. The candidate's own token is not the signal.

DECISION: `slots = max(1, int(5125 * 0.2)) = 1025`. Walk holdout ids in order. With the cost disabled, keep while a slot remains and never charge. With the cost active, a contrary keep subtracts 5 when the budget is at least 5; when the budget is below 5 the row is dropped and the slot stays open. No partial charge.

DOWNSTREAM EFFECT: the two traces. Nothing outside the root is written by the script. A second process recomputed every contrary flag from `index.jsonl` and from a fresh parse of the prefix. Index mismatches: 0.

## Causal Chain

This is a claim about a hand-specified counter, evaluated so it is not mistaken for learning.

1. Data enters. The frozen prefix is a real file read (VERIFIED).
2. An observation is created. 25624 parsed rows, with token, error flag, and prompt hash (VERIFIED). The index stores those fields and not line text (`prompt:` absent from `index.jsonl`, OBSERVED).
3. A label is generated. `contrary` is a deterministic function of earlier formation rows (VERIFIED by re-parse). It is not a new reward model.
4. A learning update. Absent. The budget change is `budget -= 5` in `run_pass` when `enabled and contrary` and the row is kept (OBSERVED in source, VERIFIED in the 20 charge rows). The function does not fit a threshold on holdout outcomes.
5. Persistence. The budget after each decision is in the root-local traces (VERIFIED). It is not written to production state.
6. Later read. The next row in the same pass reads `budget` and `slots_left` (VERIFIED: each row's `budget_before` equals the previous `budget_after`).
7. Decision change. 803 keep→drop and 575 drop→keep (VERIFIED).
8. Observable behavior. Active keeps 797 rows. Disabled keeps 1025 (VERIFIED).
9. Measurable consequence. Active spend 100. Disabled spend 0. Counterfactual bill of the disabled contrary keeps is 4115 (VERIFIED: `5 * 823`).
10. Improvement against an independent criterion. The precommitted comparison to the counterfactual bill holds: 100 < 4115. The comparison to recorded disabled spend does not: 100 > 0. Link 10 as "the policy learned to spend less" fails. The lower contrary-keep count is what the insolvency clause specifies once more than 20 contrary rows sit in the disabled keep set (VERIFIED arithmetic, not an independent gain).

## Adversarial Findings

**Static heuristic dressed as learning.** The unit checks inside `run_cost.py` use three synthetic rows and a budget of 5 to prove the code path can differ. Those checks are not the experiment. The experiment is the 5125-row holdout, with budget 100 and cost 5 frozen before that pass. Calling the 803 refusals learning would launder a `if budget < 5: drop` branch. That claim is DISPROVEN.

**Simplest alternative.** Count contrary rows among the first 1025 holdout ids. The disabled pass keeps those first 1025 regardless of token. If that contrary count is `C` and `C > 20`, the active pass must pay for the first 20, refuse the other `C - 20`, and may spend the freed slots on later rows that are still affordable. Observed `C = 823`, refusals `803`, which is `823 - 20`. The result matches that identity. It is still a prospective result: `C` was not used to choose the budget, the cost, the slot fraction, or the contrary definition.

**Slot refill mistaken for a cost on unlinked items.** `n_changes_on_non_template` in `result.json` is 335. The second process split it. Keep→drop with `formation_key_count == 0`: 0. Keep→drop with `formation_prior_count == 0`: 0. Keep→drop with `contrary` false: 0. Drop→keep with `formation_key_count == 0`: 335. Drop→keep with a formation key but no earlier formation row: 24. Drop→keep that are contrary: 0. Drop→keep with a repeated formation key and no contrary prior: 215. One remaining drop→keep has a single non-contrary formation prior. The cost gate refused only contrary rows, and only after the budget was already below 5. Unlinked rows changed by receiving a slot a refused contrary row did not take. That is the slot rule written before the run. It is not a charge against a missing signal.

**Own-token confound.** The candidate's result token does not set `contrary`. A prior formation row does. Unique prompts and prompts whose earlier formation rows are not `fail` and have no post-result `error:` field are not charged. `safety_blocked`, `invalid_syntax`, `rejected_*`, `dry_run_staged`, and `success` are contrary only when that prior-row rule matches. `import_hallucination` can qualify through its `error:` suffix. The three re-parsed samples qualified through formation id 18, token `load_failed`, which also has an `error:` suffix.

**Truncated prompts.** Many journal writers store `prompt[:80]`. The link is the hash of that stored text after whitespace collapse and a trailing `|` strip, without lowercasing. A full prompt and its 80-character prefix do not link. That false-negative rate pushes toward fewer contrary flags. It was not repaired.

**Self-confirming replay.** The script replays from the index it just wrote. The second process did not import `run_cost.py`. It re-parsed the prefix, recomputed the three links, and walked both traces. Problems list: empty. Index contrary mismatches: 0.

## Controlled Experiments

**Setup.** Snapshot prefix above. Parser: first `\bresult:\s*([A-Za-z_][A-Za-z0-9_]*)`. Holdout: matched id % 5 == 0, not used to set the budget, the cost, the slot fraction, or the contrary rule. Those constants were written into `run_cost.py` before the script was executed. Slot fraction 0.2 is the production prune fraction applied to this split, not a fit. `5125 * 0.2` is 1025.0, and `int` of that is 1025.

**Cost rule.** Budget starts at 100. After every decision the traces store `budget_before` and `budget_after`. A charge of 5 occurs only when the cost is active, the row is kept, and `contrary` is true. If the cost is active, the row is contrary, and the budget is below 5, the decision is drop, the charge is 0, and the slot is not consumed. The budget does not go negative.

**Treatment.** Cost active.
**Control.** Cost disabled. Same rows, same order, same 1025 slots. Budget stays 100.

**Observed.**

| | Cost disabled | Cost active |
|---|---|---|
| Keeps | 1025 | 797 |
| Drops | 4100 | 4328 |
| Contrary keeps | 823 | 20 |
| Final budget | 100 | 0 |
| Recorded spend | 0 | 100 |
| Slots left | 0 | 228 |

Keep→drop: 803, all contrary, all with `budget_before` of 0 and charge 0. The first of these is seq 37, id 185. Drop→keep: 575, none contrary. Decisions differ: yes. Any of those differences on a non-template item: yes, 335, all on the drop→keep side.

The 20 charges are seqs 5, 6, 7, 9, 10, 17, 21–27, 30–36, ids 25, 30, 35, 45, 50, 85, 105, 110, 115, 120, 125, 130, 135, 150, 155, 160, 165, 170, 175, 180. Budgets step 100, 95, …, 0. The twentieth charge ends at 0 on id 180. Id 185 is the next holdout row and is the first refusal.

Link samples, re-parsed:

| Holdout id | Prior signal id | Prior token | Same prompt hash | Budget before | Charged |
|---|---|---|---|---|---|
| 185 | 18 | `load_failed` | yes | 0 | 0 |
| 190 | 18 | `load_failed` | yes | 0 | 0 |
| 195 | 18 | `load_failed` | yes | 0 | 0 |

Id 18 is a formation row. It is smaller than each of those holdout ids. It has an `error:` suffix as well as a fail-class token.

**Budget arithmetic.** `recorded_spend_active = 100 - 0 = 100`. `recorded_spend_disabled = 100 - 100 = 0`. `recorded_active_spend_lt_disabled` is false. `counterfactual_charge_on_disabled_keeps = 5 * 823 = 4115`. `active_spend_lt_counterfactual` is true. The keep/drop shift reduces expenditure relative to billing the disabled keep set. The active pass still records the higher spend of the two conditions, because the disabled pass never charges.

**Why 228 slots remain.** Non-contrary holdout rows: `5125 - 4348 = 777`. Active keeps those 777 plus the 20 paid contrary rows, total 797. Every remaining candidate was contrary and unpaid, so the last 228 slots were not filled. `1025 - 797 = 228`.

**Statement.** The test showed later keep/drop decisions shifting once the budget could no longer pay the cost. The shift is the insolvency clause after 20 paid contrary keeps. It is not a learned scorer and not a production selector.

**Limitations.** File order is the base policy, so the token text does not also change which rows the slots reach. A different base policy could refuse earlier and leave a different refill set. Prompt truncation creates missed links. The live log grew past the prefix during the run; those extra bytes were not scored. Unit checks used a synthetic budget of 5 so the refusal branch is reachable in three rows; they do not estimate the holdout effect.

## Independent Review

Not required. This mission did not change production code. `feral-independent-review` was not run.

## Evidence Ledger

| ID | Claim | Label | Pointer |
|---|---|---|---|
| E1 | Prefix hash and length | VERIFIED | `result.json` `source_sha256`, `source_bytes`; second-process hash |
| E2 | Identity histograms | VERIFIED | Independent Counter; script would have exited 2 on mismatch |
| E3 | Trace arithmetic and refusal condition | VERIFIED | Second-process walk; `problems: []` |
| E4 | Full holdout contrary replay | VERIFIED | Index vs fresh parse, 0 mismatches |
| E5 | Link samples | VERIFIED | Ids 185, 190, 195 → formation id 18, `load_failed` |
| E6 | Non-template split | VERIFIED | 335 drop→keep unlinked; 0 keep→drop unlinked |
| E7 | Spend pair and counterfactual | VERIFIED | 100 vs 0 recorded; 4115 counterfactual |
| E8 | Closed-branch and HEAD stability | VERIFIED | Digests below |
| E9 | Live log tail moved during the run | OBSERVED | `SELF_EDIT.log` size 33015593 → 33015818; whole-file hash changed. Prefix at read time already matched. |
| E10 | Learning update occurred | DISPROVEN | Source of `run_pass`; 20 identical subtractions of 5 |

Trace digests, from `result.json`, recomputed by the second process over the files just written: active `bd9d369fc9915213001842fcbee0f844aa477bf35c98dcdac545c3dc104f7cd9`, disabled `5c8041c1aa500d08eee32017ead8e03242edf07a10e0ea8a477afe7095a4ec2b`.

## Final Classification

The root-local budget is a static integer policy demonstrated on one held-out slice. Links 7–9 hold inside that slice for a counter specified in advance. Link 4, a learning update, does not. Link 10 does not hold as an improvement beyond the rule's own insolvency clause. Classification of this mechanism: not L2 and not L3. It is not Level 4. Production consumption of the budget is L0: the files exist under the experiment root and no production path reads them.

## What Is Actually Proven

- The frozen prefix still hashes to `bf05736e4bf7a5a14e5d12f6cf9f3729440fa2d0b329e2ea7bb0dd21d3a89383` and still parses to the prior test's token counts.
- With the cost on, the budget goes 100 → 0 in 20 charges of 5, then refuses further contrary keeps.
- 803 held-out rows change from keep to drop. All 803 are contrary. None are unlinked. None lack a prior formation row.
- 575 held-out rows change from drop to keep. None of those 575 are contrary. 335 of them are unlinked.
- Recorded active spend is 100. Recorded disabled spend is 0. The counterfactual charge on the 823 disabled contrary keeps is 4115.
- Closed-branch hashes and Git HEAD are the same before and after the run.

## What Is Only Supported

- An append of 225 bytes past byte 33015593 cannot change the hash of the first 33008379 bytes. The prefix was hashed at the start of the run, when the file was already 33015593 bytes. It was not hashed again after the file reached 33015818 bytes. The growth is past the scored offset (SUPPORTED from the two sizes; the second prefix hash was not repeated).
- Production prune still ignores `result:` tokens. That was established in the consolidation audit and was not re-tested by running a prune. This mission added no reader.

## What Remains Unknown

- Whether a different base order, a different slot count, or a different link than exact normalized-prompt hash would still cross the 20-payment line on this prefix.
- How many true repeated tasks are missed because one side stores `prompt[:80]` and the other stores the full prompt.
- Whether a budget that stayed solvent for the whole disabled keep set would leave the keep/drop set unchanged. This slice did not provide that case. The rule allows it. The synthetic unit check shows a solvent charge with no decision change, on three made-up rows, not on this log.

## What Was Disproven

- The claim that this shift is a learned policy, or a Level 4 selector, is disproven by the source: one fixed subtraction, chosen before the holdout result existed.
- The claim that the cost dropped unlinked rows is disproven by the trace split: keep→drop on `formation_key_count == 0` is 0.
- H0 (no keep/drop difference) is disproven on this slice.

## Recommendations

Stop. Do not promote the budget into production retention, consolidation, or the closed selector. Do not chain another test from this result. A null result would have been a complete outcome. This result is also complete: the held-out decisions moved, the movement matches the precommitted insolvency rule, and the expenditure comparison is the pair above (100 against 0 recorded, 100 against 4115 counterfactual). No further experiment is authorized by this mission.

## Integrity Record

```
production changes: NO
files changed: memory/experiments/outcome_signal_cost_20261019/run_cost.py (18564 bytes); index.jsonl (7666840); budget_trace_active.jsonl (1109023); budget_trace_disabled.jsonl (1112823); result.json (1796); status.txt (91); audits/2026-10-19_outcome_signal_cost_retention.md
Git HEAD before: 4d2932c5f9a74e46ac866862ac4972b0787d7b8f
Git HEAD after: 4d2932c5f9a74e46ac866862ac4972b0787d7b8f
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: python3 run_cost.py (exited 0); two later python3 recheck processes (exited 0). No long-running process left.
configuration changes: NO
test changes: NO
temporary files created: none on disk (rechecks were stdin scripts)
temporary files cleaned: YES
orphaned processes: checked, none found
known anomalies: The worktree was already dirty before this mission (many pre-existing modified and untracked paths). This mission did not stage or commit them. During the run the live server appended memory/SELF_EDIT.log from 33015593 bytes (SHA-256 f42ea7a2ef5b1b4c2806ea856a2757401cf854acde661b9b1d18f75bdc8ce658) to 33015818 bytes (SHA-256 b9542b6310be71d11fa64f68ec93623b108d4a56e45168c0b42a7c8be19ab0fd). memory/self_model.json stayed 19495 bytes and its hash changed from 6c56ecf6ef341efc0b49b0040aca92ea492d3d0c7dd4354d131e87199ba7b3b6 to 4536aec6a970dece91fd1c90a1440c05267ebf5c4140729199bb26b0df1dedf6. memory/memory_meta.json (121297324, d73df4d84e7d570f7343ad627dda1ecc659587ee8f25404703f27e65d40c4570), memory/faiss.index (222015021, fa0baa1f9ea724623f09453ad23924a7fc73aafce0f5e49b7772a7e06a6e0447), memory/consolidation_log.jsonl (455994, 8d434a381d16a4311f91b18aa83baffc0639cc540446cf997331e611994289b1), and memory/memory_journal_active.log (0 bytes, e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855) were unchanged across the run. Those live writes are the running server, not this experiment.
known deviations from requested methodology: none. The second process reimplemented the parser instead of importing run_cost.py. Constants were not retuned after the result.
```

Closed-branch hashes, identical before and after:

| Path | Bytes | SHA-256 |
|---|---|---|
| `app/experiments/persistent_routing/selector.py` | 5149 | `71f6f04fa522c78c49ea8eddeb67373335d8f6ea6b574c29220f0379fe0c6127` |
| `memory/experiments/persistent_routing/log_E_experience.jsonl` | 5486 | `4f5bb2377035a3ce94a1c21df6aa83e7f000e45a44e32eb296b01fa4968f0241` |
| `memory/experiments/strategy_characterization/stage1/log_stage1.jsonl` | 165572 | `7f9d9533cc05add8171eae632f3c9be7678233c2424ef7810858a64e1b4f826a` |
| `memory/experiments/richer_experience_20261019/log_E_experience_rich.jsonl` | 76571 | `547f17b3da8aecfa2b0e1dbeeba36db23990cf9f0dc0e6181e7e60e33aa7f7be` |
| `audits/2026-10-19_richer_experience_capture.md` | 10612 | `1b66ed539fb856bc6c33bbccbebe776369d55b730d37ea88b6ae2131d81ac71f` |
| `audits/2026-10-19_self_edit_token_visibility.md` | 13323 | `e82d5668780bc5897edb73ed32722999bdccd0e1315c2a42d769aba7c3c5d722` |
| `audits/2026-10-19_memory_consolidation_outcome_signal.md` | 12813 | `bf1cc7ef6b39dbbe3f85ced18eb8304425e1ab36f3106b92e92adddb54e8c921` |
| `audits/2026-10-19_outcome_signal_relay_comparison.md` | 11078 | `f7e5b8d7351c716f44b95b74e02e988b33ed9cfa05aa6d9d677ca8bc4124fbfc` |
| `app/core/echo_model_orchestrator.py` | 90538 | `6dcc8b90a33008e889821f1e41058cd6291fca754ee6418fb30444a0e99b0720` |
| `app/core/river_deliberation.py` | 81478 | `c7d68f6e09458007f230bb00138738c1115a70fc919aab1fb3717220724370cc` |
| `grok_relay/from_m5.md` | 12054 | `d3fe00fc485068d01f95dfe1615d4d8405d18f7fc96fbe3915af89662338f93c` |
| `grok_relay/.outbox.jsonl` | 548 | `c1f5102d99f8fc29bc5ee204154edc14e0439509bdd904a653f8e6a5b0cad17d` |
| `grok_relay/.last_seen_from_ark.json` | 91 | `8dddc033cd5869a0007cc711bd771124ae9303a2e15d392631f16272b15b882f` |
| `grok_relay/.inbox_from_ark.md` | 3871 | `10b5363bac7f675b720b242a744a3b6bd765be2f863e7625286fa73efe9ae3c4` |

Identical SHA-256 to the prior measurement fixes those byte lengths. This pass re-measured the relay cursor: `grok_relay/.last_seen_from_ark.json` is 91 bytes.
