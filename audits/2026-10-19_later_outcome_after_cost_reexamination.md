# Re-examination: Later Outcome After the Cost Rule

Date: 2026-10-19. Investigation only. The sealed audit `audits/2026-10-19_later_outcome_after_cost.md` is left unchanged.

inconclusive: comparison confounded by differential missingness and non-overlapping keep sets; the cost rule does not create the missing keys.

The conditional rates in the sealed audit are real counts of later log tokens, and they are lower for the cost-on keep set (140/349 versus 670/787). That comparison is only among rows that already have a later token. Cost-on is missing that token on 420 of 769 scored keeps (55%). Cost-off is missing it on 92 of 879 (10%). The two sets are different survivors. On the 194 keeps shared by both rules, the later token is the same row for row, so the shared rows show no outcome difference and no outcome gain. The full-set gap is the non-overlap: cost-on adds keeps that are mostly missing, and cost-off keeps a different present subset. Counting every missing row as failure, or every missing row as success, leaves the cost-on minus cost-off sign negative, including the bound most favorable to cost-on. Those bounds are arithmetic, not observations, and they still compare different rows. The 335 keyless refills are all missing, which is why dropping them leaves 140/349 versus 670/787 unchanged; they were never in that denominator, so the drop does not test selection bias. The empty keys are continuation lines of multiline journal writes. The cost rule only retains rows whose keys were already empty. Exact-success is the self-edit pipeline's own journal label, so every outcome number below is provisional against an independent ground-truth scorer. No outcome gain is shown. The supportable statement is that the comparison is confounded by differential missingness.

## Step 1. Sensitivity on the frozen scored rows

Source: `memory/experiments/later_outcome_after_cost_20261019/scored_trials.jsonl` (1822 lines). Recomputed 2026-10-19 from that file with integer cross-products and `decimal.Decimal`. No new model output. No imputation is listed as observed.

Scored keeps, after the sealed charging-key exclusion: cost-on 769 (797 keeps, 28 excluded), cost-off 879 (1025 keeps, 146 excluded). Present means a later same-key token exists. Success means that token is exactly `success`.

| Check | Label | Cost-on | Cost-off | Rate on | Rate off | Delta (on minus off) | Cross-product | Sign |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| (a) Present only | observed conditional | 140/349 | 670/787 | 0.4011461318051575931232091691 | 0.8513341804320203303684879288 | -0.4501880486268627372452787597 | 110180 vs 233830 | lower |
| (b) Missing as failure | bounded | 140/769 | 670/879 | 0.1820546163849154746423927178 | 0.7622298065984072810011376564 | -0.5801751902134918063587449386 | 123060 vs 515230 | lower |
| (c) Missing as success | bounded | 560/769 | 762/879 | 0.7282184655396618985695708713 | 0.8668941979522184300341296928 | -0.1386757324125565314645588215 | 492240 vs 585978 | lower |

The sign of cost-on minus cost-off is the same under (a), (b), and (c). It is lower in all three. The same sign does not establish "cost rule worse." (b) and (c) assign outcomes to rows that have none. (a) drops those rows. Neither operation puts the same keeps in both arms.

Two extra bounds, also bounded, not substitutes for (a)-(c):

| Bound | Label | Cost-on | Cost-off | Delta | Cross-product | Sign |
| --- | --- | --- | --- | --- | --- | --- |
| Best case for cost-on: missing-on as success, missing-off as failure | bounded | 560/769 | 670/879 | -0.0340113410587453824315667851 | 492240 vs 515230 | lower |
| Worst case for cost-on: missing-on as failure, missing-off as success | bounded | 140/769 | 762/879 | -0.6848395815673029553917369750 | 123060 vs 585978 | lower |

Even the assignment most favorable to cost-on stays lower. That is still a comparison of different rows.

Observed overlap, from the same file. After charging-key exclusion, 194 ids are kept under both rules. The triple `(missing, later_id, later_token)` differs on 0 of those 194. Present 113, missing 81, exact-success 103. The difference on this subset is zero.

Observed non-overlap:

| Subset | n | Present | Missing | Exact-success |
| --- | --- | --- | --- | --- |
| Kept only by cost-on | 575 | 236 | 339 | 37 |
| Kept only by cost-off | 685 | 674 | 11 | 567 |

Check sums, observed: cost-on present 113+236=349, success 103+37=140, missing 81+339=420. Cost-off present 113+674=787, success 103+567=670, missing 81+11=92. The conditional gap is this mixture. The later tokens were already in the log. Selecting a different subset changes the rate without changing any logged outcome.

## Step 2. Missingness

Observed, joined to the frozen cost index and to a reparse of the pinned log prefix. Every missing scored row has zero same-key successors inside the pin (`missing_with_later_in_pin = 0`). The result does not depend on the live tail past the pin.

Cost-on missing, 420 rows:

| Cause | n | What they are |
| --- | --- | --- |
| No formation key (`refill_335`) | 335 | All `formation_key_count == 0`, all absent from the cost-off scored keeps (disabled drop, active keep), all missing. | Own tokens: `staging_import_failed` 178, `success` 97, `load_failed` 32, `invalid_syntax` 27, `proposed_core_edit_for_review` 1. Empty prompt key 329. Nonempty key 6 (length 80: 1, length 1-79: 1, length 81 or more: 4). The 6 nonempty tokens are `success` 4, `staging_import_failed` 1, `proposed_core_edit_for_review` 1. Writers that store `prompt[:80]` account for 1 of the 335. Writers that store the full prompt account for 334. |
| Remaining | 85 | 81 are the overlap missing rows, missing under cost-off with the same later fields. 4 are cost-on only. `formation_key_count == 0` on 74 (the keeps both rules already shared). `formation_key_count > 0` on 11. Empty key 71. Nonempty and still no later record 14. Own tokens: `success` 74, `load_failed` 8, `rejected_meaningless_prompt` 2, `proposed_core_edit_for_review` 1. Key length 0: 71, exactly 80: 3, 81 or more: 11. The three length-80 tokens are `rejected_meaningless_prompt` 2 and `proposed_core_edit_for_review` 1. The 4 cost-on-only rows are all nonempty and all `formation_key_count > 0` (counts 20, 11, 31, 1; lengths 105, 80, 80, 80; tokens `rejected_meaningless_prompt` 2, `success` 1, `proposed_core_edit_for_review` 1). Truncating writers: 3 of 85. Full-prompt writers: 82 of 85. |

Cost-off missing, 92 rows:

| Cause | n | What they are |
| --- | --- | --- |
| Shared with cost-on | 81 | The same 81 overlap rows. 74 have `formation_key_count == 0`. 7 have `formation_key_count > 0`. |
| Cost-off only | 11 | All 11 are contrary keeps, all nonempty, none have `formation_key_count == 0`. Tokens: `success` 9, `load_failed` 2. |
| No-formation-key refills | 0 | The 335 refills are not in the cost-off keep set. |

Cost-off missing totals: `formation_key_count == 0` on 74, all missing; `formation_key_count > 0` on 18. Empty key 71. Nonempty and no later record 21. Own tokens overall: `success` 82, `load_failed` 10. No length-80 key in the cost-off scored set. Truncating writers: 0. Full-prompt writers: 92. Contrary among the 92: 11. Not contrary: 81.

Counts for properties the cost rule acts on, among scored keeps:

| Property | Cost-on (n missing / n) | Cost-off (n missing / n) |
| --- | --- | --- |
| `formation_key_count == 0` | 409/409 | 74/74 |
| `formation_key_count > 0` | 11/360 | 18/805 |
| Empty prompt key | 400/400 | 71/71 |
| Refill (`refill_335`) | 335/335 | 0/0 |
| Contrary | 0/0 scored | 11/685 |
| Not contrary | 420/769 | 81/194 |
| Overlap | 81/194 | 81/194 |
| Arm-only | 339/575 | 11/685 |

Missingness tracks `formation_key_count == 0` and the empty prompt key. Every scored row with either property is missing, in both arms. The 9 cost-on `formation_key_count == 0` rows that are not empty keys are also all missing (6 inside the 335, 3 inside the 85): a nonempty key with no formation-split record sharing it. Refill status tracks missingness because every refill has `formation_key_count == 0`. The contrary flag does not. Cost-on scored keeps contain 0 contrary rows. Cost-off contrary keeps are present on 674 of 685.

Task type is absent. Scored rows have no task-type field. Of 25675 matched records in the pin, 0 sit on a physical line containing the substring `task_type`. The pin contains that substring on 31 physical lines, none of them a matched result line. Correlation with task type is UNKNOWN. No value was filled in.

## Step 3. Root cause of the keyless refills

The cost rule does not create or strip formation keys. Keyless holdout rows exist under both decisions. The cost rule over-represents them by freeing slots.

Holdout universe, observed from the frozen traces and index: 5125 holdout rows, 409 with `formation_key_count == 0`, 400 of those with an empty prompt key. Disabled keeps 74 of the 409. Active keeps all 409. Kept by both: 74. Drop under disabled and keep under active: 335. Keep under disabled and drop under active: 0. The cost rule never drops a keyless row that the disabled rule kept. It adds the 335 when a freed slot reaches them. The 74 kept by both are exactly the cost-off scored keyless set, and they are all missing, so keyless missing rows exist with the cost disabled.

Where the empty key is born, upstream of either pass:

- `memory/experiments/outcome_signal_cost_20261019/run_cost.py` lines 99-106. `prompt_key` returns `""` when the physical-line prefix before the result span has no `prompt:` marker.
- Same file, line 249. `parse_records` calls `prompt_key` on that one physical line.
- Same file, lines 263-277. `attach_signals` sets `formation_key_count` to 0 when the sha is empty, and also when no formation-split record shares a nonempty sha. This assignment happens before `run_pass`.
- Same file, lines 124-135. `run_pass` copies `formation_key_count` into the trace. It keeps or drops from slots, the contrary flag, and the budget. It does not write prompt text and it does not recompute the key.
- Same file, lines 210-221. The unit example is the slot-freeing pattern: with one non-template row (`formation_key_count` 0) after two contrary rows, disabled decides keep, keep, drop and active decides keep, drop, keep. The third row was already keyless. The active pass retains it.

Where the physical line loses the marker:

- `app/core/memory_bridge.py` lines 155-156. `append_to_journal` writes one `f"[{timestamp}] {echo_text}\n"`. A newline inside `echo_text` starts another physical line. Only the first physical line receives the timestamp wrapper.
- `app/core/self_edit_manager.py` writes the full prompt, which can contain newlines, at lines 2187 (`invalid_syntax`), 2204 (`staging_import_failed`), 2325 (`load_blocked`), 2333 (`success`), and 2358 (`load_failed`). The `prompt[:80]` writers (lines 1988, 2052, 2063, 2232, 2279, 2690) are a different truncation. They account for 1 of the 335 refills and 3 of the 85, not for the 329 empty-key refills.

Structural reparse of the pin, 2026-10-19, no prompt text printed. Prefix hash and pin hash matched the sealed later-outcome audit before this classification. Of the 400 holdout rows with an empty prompt key: `prompt:` appears on that physical line in 0; the line contains `| result:` in 400; the line matches a journal timestamp in 0; 149 start with `[` and none of those 149 are journal-timestamp lines. The nearest earlier journal-timestamp line contains `prompt:` for all 400, and that anchor is a different physical line for all 400. Gap from the timestamp line to the result line: 1 on 60 rows, 3 on 81, 4 on 28, greater than 5 on 231. Gaps of 2 and of 5: 0. Own tokens of the 400: `staging_import_failed` 177, `success` 157, `load_failed` 39, `invalid_syntax` 27. Marker pattern on those lines: error field and no `timestamp:` word, 216 (`staging_import_failed` 177, `load_failed` 39); `timestamp:` word and no error field, 157 (the success rows); neither, 27 (`invalid_syntax`).

That is the parser reading the physical line where `| result:` landed after a multiline prompt. The retention path never had the key.

Fix status. No formation-key-preserving fix exists inside the cost rule's retention path, because that path does not hold the key to preserve. No fix was described as a patch, none was prototyped, and none was applied to production. A change to the journal writer or to the line parser would sit outside this retention path and outside this audit. It was not built.

## Step 4. Fresh comparison

Not run. Step 3 did not yield a fix that preserves formation keys. No pre-registration file was written. No new sample was collected. No model was called.

## Step 5. Scorer

Exact-success in this measurement is the next logged token being exactly the string `success`. `measure_later.py` defines that comparison. It does not import `echo_ground_truth.py`.

The string is written by the pipeline itself. `app/core/self_edit_manager.py` line 2333 appends `result: success` only after `load_self_edit_module()` returns a module (lines 2316-2333). The fitness comparison that can block that write calls `echo_quality_scorer._score_response_quality` (`echo_quality_scorer.py` line 344) with `task_type` hardcoded to `"coding"` (`self_edit_manager.py` lines 2258-2268). On the coding path that function is an AST-complexity heuristic. Its own comment states that incorrect control flow is undetectable without execution (lines 368-369). On an exception the fitness gate fails open and deployment continues (`self_edit_manager.py` lines 2294-2298).

This is the pipeline's own journal label. It is not Echo's conversational self-rating, and it is not an independent ground-truth check in the style of `echo_ground_truth.py`. Every outcome number in this file is provisional against that independence standard. The counts remain valid counts of subsequent logged tokens.

## What this evidence does not support

- "Cost rule worse" as a causal claim about later edit quality. The conditional rate is lower, and the sign stays lower under both imputations, on non-overlapping keep sets.
- "Cost rule better."
- "Cost rule not different" on the full keep sets. The conditional rates differ. Identity holds on the 194 shared keeps only.
- An outcome gain for the cost rule. The shared rows are identical. The added cost-on rows are mostly missing.
- The claim that the cost rule destroys formation keys. DISPROVEN by the writer, the parser, and the 74 keyless rows the disabled rule already keeps.
- The claim that dropping the 335 refills tests selection bias. They were never in the conditional denominator.
- Treating the secondary non-failure rate as an outcome gain. This re-examination does not use it. The sealed audit already recorded that it disagrees with exact-success because `rejected_meaningless_prompt` is common on the cost-on present rows and is not a fail or error token.
- A learned scorer, a budget that production reads, or any redesign, demotion, or retirement of a project claim.
- An independent ground-truth outcome. The numbers are provisional, as Step 5 states.

What would change the verdict is a comparison of the same items under both rules with non-differential missingness, or a key-preserving rerun whose metric, sample size, and decision rule were pre-registered before data collection. That rerun was not authorized by Step 3, and it was not run.

## Relation to the sealed audit

`audits/2026-10-19_later_outcome_after_cost.md` stays the historical record of the conditional measurement (28671 bytes, SHA-256 `b5cc2ac38343bf010574bc37146dd9b4f9e2612cc2322474ba5e5b0bdbbce740`, reconfirmed at the before snapshot below). Its conditional counts match this recomputation. Its causal reading, that the retention shift produced worse later outcomes, is not identified by those counts. This file does not edit that one.

## Hashes before this write

Taken 2026-10-19T22:18:57Z. Git HEAD `4d2932c5f9a74e46ac866862ac4972b0787d7b8f`.

The frozen prefix and the pinned read were reconfirmed against the live log immediately before this snapshot. Prefix: 33008379 bytes, SHA-256 `bf05736e4bf7a5a14e5d12f6cf9f3729440fa2d0b329e2ea7bb0dd21d3a89383`, ends on a newline. Pin: 33055479 bytes, SHA-256 `f859b8ca2f0f84e583a204834d5ced81d70eb0cfee92bb5eec741305c20677b1`. Pin reparse: 170819 physical lines, 25675 matched records, 1 unparsed. Closed-branch and frozen-experiment hashes match the sealed later-outcome audit. Live production files had already moved since 2026-10-19T22:14:52Z because the server is running. That drift is recorded here as the before state of this write.

| Bytes | SHA-256 | Path |
| --- | --- | --- |
| 5149 | 71f6f04fa522c78c49ea8eddeb67373335d8f6ea6b574c29220f0379fe0c6127 | app/experiments/persistent_routing/selector.py |
| 5486 | 4f5bb2377035a3ce94a1c21df6aa83e7f000e45a44e32eb296b01fa4968f0241 | memory/experiments/persistent_routing/log_E_experience.jsonl |
| 165572 | 7f9d9533cc05add8171eae632f3c9be7678233c2424ef7810858a64e1b4f826a | memory/experiments/strategy_characterization/stage1/log_stage1.jsonl |
| 76571 | 547f17b3da8aecfa2b0e1dbeeba36db23990cf9f0dc0e6181e7e60e33aa7f7be | memory/experiments/richer_experience_20261019/log_E_experience_rich.jsonl |
| 10612 | 1b66ed539fb856bc6c33bbccbebe776369d55b730d37ea88b6ae2131d81ac71f | audits/2026-10-19_richer_experience_capture.md |
| 13323 | e82d5668780bc5897edb73ed32722999bdccd0e1315c2a42d769aba7c3c5d722 | audits/2026-10-19_self_edit_token_visibility.md |
| 12813 | bf1cc7ef6b39dbbe3f85ced18eb8304425e1ab36f3106b92e92adddb54e8c921 | audits/2026-10-19_memory_consolidation_outcome_signal.md |
| 11078 | f7e5b8d7351c716f44b95b74e02e988b33ed9cfa05aa6d9d677ca8bc4124fbfc | audits/2026-10-19_outcome_signal_relay_comparison.md |
| 23651 | 00e7c5a61c94464e9479be5201d66dee49586e370949351b18309633916f13e8 | audits/2026-10-19_outcome_signal_cost_retention.md |
| 19824 | 6cf64b91ff5350c409bef198a687d33bd08969ba0fd80a418953feeb79843d9f | audits/2026-10-19_outcome_signal_cost_ceiling.md |
| 28671 | b5cc2ac38343bf010574bc37146dd9b4f9e2612cc2322474ba5e5b0bdbbce740 | audits/2026-10-19_later_outcome_after_cost.md |
| 12054 | d3fe00fc485068d01f95dfe1615d4d8405d18f7fc96fbe3915af89662338f93c | grok_relay/from_m5.md |
| 548 | c1f5102d99f8fc29bc5ee204154edc14e0439509bdd904a653f8e6a5b0cad17d | grok_relay/.outbox.jsonl |
| 91 | 8dddc033cd5869a0007cc711bd771124ae9303a2e15d392631f16272b15b882f | grok_relay/.last_seen_from_ark.json |
| 3871 | 10b5363bac7f675b720b242a744a3b6bd765be2f863e7625286fa73efe9ae3c4 | grok_relay/.inbox_from_ark.md |
| 90538 | 6dcc8b90a33008e889821f1e41058cd6291fca754ee6418fb30444a0e99b0720 | app/core/echo_model_orchestrator.py |
| 81478 | c7d68f6e09458007f230bb00138738c1115a70fc919aab1fb3717220724370cc | app/core/river_deliberation.py |
| 1796 | c2174b9b8bfa38647a0954c949632ffcbc8510a74d35a1e7dad572dc45762983 | memory/experiments/outcome_signal_cost_20261019/result.json |
| 7666840 | 2f6ed01a125d5951cd61ae95004c68cd53fdfdc07e46c1cb476f2a64d97e3d58 | memory/experiments/outcome_signal_cost_20261019/index.jsonl |
| 1109023 | bd9d369fc9915213001842fcbee0f844aa477bf35c98dcdac545c3dc104f7cd9 | memory/experiments/outcome_signal_cost_20261019/budget_trace_active.jsonl |
| 1112823 | 5c8041c1aa500d08eee32017ead8e03242edf07a10e0ea8a477afe7095a4ec2b | memory/experiments/outcome_signal_cost_20261019/budget_trace_disabled.jsonl |
| 91 | 339cd4cbfca37fa12e94e6096b27dd78994e5df59c652fc4bde08313eadd532d | memory/experiments/outcome_signal_cost_20261019/status.txt |
| 18564 | c0aab29d991679b2915722dbcb6ccd46475910a25e087aba353a7ae7a3d31b18 | memory/experiments/outcome_signal_cost_20261019/run_cost.py |
| 10191 | e5b0944e2328389aff7eaad70852d209c9a9c0c6c41ddf49380f907ab513ad6d | memory/experiments/later_outcome_after_cost_20261019/result.json |
| 602826 | bdf01f468d056f244e6ba2941f68d17c5a87d7a9939651071e746355455a3556 | memory/experiments/later_outcome_after_cost_20261019/scored_trials.jsonl |
| 256 | b55a91daace45da367c968f5687220a82461218e4e92c81cf97aae01f999293d | memory/experiments/later_outcome_after_cost_20261019/verify.json |
| 22051 | b6a717f0dc3466d83ee0030fc0d79d8c99b9f40a9cfd9bd51c29d7f843b53323 | memory/experiments/later_outcome_after_cost_20261019/measure_later.py |
| 8549 | b3fede785468237d9ba5c57750616f0cdcaf838d8b4db8a4a19a5c115084b1ca | memory/experiments/later_outcome_after_cost_20261019/verify_later.py |
| 33060088 | e6d7fa3ba844c4cc35595e03d56327675387fc8f48a5a188abd9c01c08a71ac6 | memory/SELF_EDIT.log |
| 121533834 | de1d9fb81176f94223240a7a686f865970e7b5a4d7e25c17e3fdfae8b88c1f3f | memory/memory_meta.json |
| 222256173 | 01322015297baa9334b4895e76127d8404b529e1d6da6e83cbe4bc1a9593498f | memory/faiss.index |
| 456936 | 8031bacfb2e06a236517fc3375d2909b6453d09987b4f8bbcc7ca2f4d5413b3f | memory/consolidation_log.jsonl |
| 19494 | b7226c8e96bc5db52c9dc66e5ddcd821e34cc42f13ba61a5ed9776731471b682 | memory/self_model.json |
| 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | memory/memory_journal_active.log |

After-write byte size and SHA-256 of this file, and the after snapshot of the same paths, are in `audits/2026-10-19_later_outcome_after_cost_reexamination.sha256.txt`. That sidecar is written after this file's final byte. This file does not contain its own digest. The sidecar does not contain its own digest.

## Integrity record

production changes: NO
files changed: this audit; the sidecar named above is written after this file is sealed
Git HEAD before: 4d2932c5f9a74e46ac866862ac4972b0787d7b8f
Git HEAD after: recorded in the sidecar after this file is sealed
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: short-lived python3 processes for counting and hashing; each exited
configuration changes: NO
test changes: NO
temporary files created: none
temporary files cleaned: YES
orphaned processes: none started that were left running
known anomalies: between 2026-10-19T22:14:52Z and the 22:18:57Z before snapshot, live memory/SELF_EDIT.log, memory/memory_meta.json, memory/faiss.index, and memory/self_model.json changed size. The server was already running. Closed-branch hashes and both frozen experiment roots did not change. Prefix and pin hashes still matched.
known deviations from requested methodology: Step 4 was not run because Step 3 found no key-preserving fix inside the cost-rule retention path. No prototype branch was created. No missing later token was filled in and then called data. The sealed 2026-10-19 later-outcome audit was not overwritten.
