# Retained learning net-utility test

Infrastructure work began October 6; boundary qualification and workload execution completed October 7, 2026, PDT. Raw evidence: [retained_utility_20261006/](retained_utility_20261006/).

## Result

**Access to retained Skill A produced no observed correctness advantage on the frozen 44-task workload.** Both conditions solved **25/44 tasks (56.8%)** and failed 19. There were **0 treatment wins, 0 control wins, 25 correct ties, 19 incorrect ties, 0 fixes and 0 regressions**. Every generated source body remained unchanged by the retained consumer.

This is a completed measurement, not another infrastructure stop. However, Skill A matched **0/44** candidates, so the experiment did not exercise an actual learned repair. It does not establish that reuse is generally neutral, beneficial or harmful. The preregistered primary disposition is **INCONCLUSIVE**; the narrower observation is **zero net correctness benefit in this cohort**.

The frozen trigger for defect-gated condition C was at least one actual unchanged-VSL application. That trigger was not met. C was not implemented or run; the workload and matcher were not changed to manufacture an intervention.

## Scope and causal contrast

This measures the **unchanged production VSL consumer in a fixed local-model code-generation harness**, not every part of running Echo. The in-scope experience-derived state is the currently ACTIVE, qualified **Skill A v4**. The same consumer, scaffolding, model output, test inputs and evaluator are used in both conditions; only that skill file's availability differs.

| Channel | Treatment |
|---|---|
| Skill A, `K2.T5.tag_priority_direction.v4.json` | In scope; exact production record copied into retained room, absent from control |
| Skill B, `K2.T2.discovered_via_accumulation_test.v1.json` | Excluded from both; experimental candidate, not ACTIVE production state |
| Matcher, schemas, runtime, adapter, model weights | Nonlearning scaffolding, identical in both rooms |
| RiverBrain, retrieval/FAISS, live self-model and other mutable runtime state | Excluded from both; not qualified causal learning channels in this experiment |
| External relays | No dependency, participation or calls |

Skill A SHA-256: `aa00c0aee4563f25254f624255605afb5448ebfb8a08c0b4833fb6796a098e7e`. Skill B SHA-256: `0f272efdaeb531ace9fe461a2b67651bfdf8d5a5601e0f3a2583751c56fd4d20`.

A's production record retains its acquisition provenance: failing candidate index 1, passing index 3, source task K2.T5, subsequent prospective validation and narrow promotion. That history qualifies it for the treatment; those selected historical successes were not counted as new net-utility evidence. See the [record](../memory/skill_ledger/skills/K2.T5.tag_priority_direction.v4.json) and [original acquisition report](2026-09-27_verified_skill_ledger_mvk_first_run_report.md).

The causal path tested was:

`same generated candidate → available ACTIVE skill records → unchanged AST matcher/consumer → final candidate → independent task correctness`.

The observed chain stopped at **no structural match**. Availability and consultation were verified; application, source change and outcome change did not occur.

## Opening integrity and preserved baseline

[Opening record](retained_utility_20261006/opening.json): branch `vsl-implementation`; HEAD `e5acbb09cece8d1791fa6d967fe57067137a8cff`; cached origin/main `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`; ahead 4 / behind 0 without fetch; empty staging. The 14 pre-existing tracked modifications and unrelated untracked artifacts were preserved.

All **203 original authority pins matched**. Including the preceding failed experiment and report, this mission pinned **262 historical/source authority files**. Live mutable files were classified separately and never supplied as experimental input. The previous [MEASUREMENT-BLOCKED report](2026-10-06_retained_net_utility_defect_gated_reuse.md), failed traceback and protocols remain unchanged.

Both experimental consumers explicitly used `VSL_ENABLED=true`, `VSL_MODE=active`. This tests the existing active-mode consumer; it does not establish that live Echo currently has active mode enabled. The control retained the same enabled consumer with an empty skill store. It did not lose its model, tools, prompt budget or ordinary scaffolding.

## Cleanup correction and durable evidence qualification

The old guard's false denial was reproduced on a harmless disposable symlink. Its path canonicalization followed the final link during `unlink`, confusing removal of an authorized directory entry with modification of the protected target.

[guard_v3.py](retained_utility_20261006/guard_v3.py) is an additive, research-only correction. **Only `os.remove` authorization changes:** resolve parent directories and any directory descriptor, then check the final directory entry without following that leaf. Target-following writes, protected renames/replacement, symlink creation and other restrictions retain their earlier policy. No production guard, sandbox or evaluator source changed.

The [frozen cleanup protocol](retained_utility_20261006/cleanup_protocol.json) and raw [old-guard](retained_utility_20261006/out/cleanup_old/result.json) / [new-guard](retained_utility_20261006/out/cleanup_new/result.json) results establish:

- Authorized absolute, relative, chained and directory-FD-relative scratch-link deletion succeeds under the corrected guard.
- Direct protected-target deletion/write, writes through a link or linked parent, replacement/rename of the target, and production Skill A write-open remain denied.
- Rename of a target-pointing scratch link and symlink creation/retargeting routes remain conservatively denied by the controller. No general permission to manipulate protected-target links was introduced.
- Ordinary scratch writes succeed; protected bytes remain unchanged.
- Both successful-child and candidate-error evaluations finish cleanup under the corrected guard.

All **16 corrected operation controls** matched their frozen expectations. These controls qualify pinned trusted-controller operation, not arbitrary malicious native controller code or adversarial concurrent path races. Candidate execution remains separately kernel confined.

[Durable result capture](retained_utility_20261006/durable_evaluator.py) journals and `fsync`s launch observations before returning them to E0.1, and journals the unchanged trusted comparator's result before cleanup. It preserves metadata, inputs, expected values in controller-only storage, stdout/stderr, child return status, timing and comparator outcome. Under the **old, still-failing cleanup guard**, both `CORRECT` and `CANDIDATE_ERROR` results survived on disk even though `run_case` could not return. Those expected failure controls distinguish candidate failure from later cleanup failure. The original failed historical recording was not rewritten or reconstructed by assertion.

## Boundary qualification

[RNU-E01-SINGLE-v4](retained_utility_20261006/boundary_v4.py) preserved the previous frozen criteria and executed **28 candidate calls**: both rooms' filesystem/arithmetic controls, then six reference/confined semantic pairs in each room. [All passed](retained_utility_20261006/out/boundary_result.json), at 10:04 PDT October 7.

Own-root reads and scratch calculation succeeded. Original Skill A/B, the opposite room, hidden canary and historical result reads were denied; production/surrogate write-opens and hidden-canary symlink reads were denied. The prior literal-root-directory startup permission remained narrowly scoped; root-relative opens of protected descendants were denied.

Structured correctness, incorrect value, bool/int distinction, candidate exception, unsupported result and timeout yielded exactly equal reference/confined evaluator results in **both rooms**. E0.1 evaluator/worker source, interpreter, isolation flags, minimal environment, JSON protocol, expected-value handling, comparison and timeouts were unchanged. The observer changes recording, not scoring. This is bounded behavioral equivalence, not proof for every possible program.

Fresh trial roots then passed a [separate frozen preflight](retained_utility_20261006/out/preflight/result.json): retained loaded exactly A, control loaded no skills, unchanged consumer code returned a harmless synthetic input unchanged, and both trial rooms passed the same filesystem controls. Each VSL consultation ran in its own confined child, separately from E0.1; the failed nested sandbox composition was not used.

## Prospective freezes

| Artifact | SHA-256 |
|---|---|
| Cleanup qualification | `27b44b9412772e15eecaa47320f07efe497426bf1cfe05570d807e31579f5433` |
| Two-room qualification | `d0f4825408860929ef0f7f8cd1cc57e582c7b2923849a4361e2c7d3b228d3742` |
| [Selection protocol](retained_utility_20261006/selection_frozen.json) | `3fc0271cebb5e192954e003372cd241a221cb9d68797607219d485fc11e4c6ee` |
| [Exact workload](retained_utility_20261006/workload.json) | `2fad039efc3e6583c874748d5178b093b04121ebf017f41bfb46bbce55a1ac44` |
| [Retained/control protocol](retained_utility_20261006/trial_protocol.json) | `3e1527da3c958316378751c10ac2addf101b79f0b3ae9f916c4cde9801615f2a` |

Selection was frozen before building the new instances. The complete task/case set, generation requests, model, budgets, arm behavior, scoring, stopping rules and conditional C policy were frozen before inference. [Analysis source](retained_utility_20261006/analysis_source_freeze.json) was pinned before baseline evaluation. No protocol or source was edited after its execution results.

## Workload independence, provenance and limitations

Selection was a **census of distinct base tasks** in the pre-existing [AP-0 v2 registry](../app/experiments/accumulation_probe/tasks_v2.py), retaining its first entry per base. It did not query VSL or filter for matching repairs. This registry spans categorization, ranking, state updates and unrelated tasks; its v2 families are documented in [September 21 preregistration](2026-09-21_ap0_stage1_preregistration_v2_DRAFT.md), before Skill A acquisition. The source was committed later in `e022b761ea57ab50bcf8f4a4360a7ef7bfdbb92d` as a missing dependency; commit date alone is not the evidence of original experimental use.

The registry has 60 entries and 45 distinct base implementations. One was excluded **before inference**: U11/invert_dict returns integer dictionary keys unsupported by unchanged E0.1. No performance-based exclusions occurred.

| Stratum | Tasks | Correct, each arm |
|---|---:|---:|
| K1 categorization | 13 | 2 |
| K2 ranking | 10 | 2 |
| K3 state updates | 10 | 10 |
| General-purpose | 11 | 11 |
| **Total** | **44** | **25** |

The 33 convention tasks use freshly generated world data, seed `202610071`; task order uses `202610072`. Implicit site conventions were fully supplied in the task specification to both conditions so the model was not being asked to guess missing facts. The 11 generic specifications can be historically seen. **All task families are historically familiar**; no claim of globally untouched domains is made. Exact provenance and original registry identity appear on every workload item.

Each task has 12 frozen VAL and 24 TEST cases from separate deterministic streams. VAL/TEST input overlap was rejected before evaluation. Repeated draws inside a partition are retained and disclosed; they are not independent evidence. Primary sample size is 44 tasks, not 1,056 cases or 2,112 executions.

Expected values come from pre-existing reference implementations, not Skill A, its transformation or model answers. Reference sources and answers remain outside the candidate roots and model requests. Tuples normalize to JSON lists; integer-key dictionaries were refused rather than silently coerced. This is test-suite correctness, not exhaustive proof of program correctness.

## Matched generation and execution

Model: **qwen2.5-coder:7b**, 7.6B, Q4_K_M. Manifest SHA-256 `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`; model-weight blob SHA-256 independently checked as `60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463` (4,683,074,048 bytes).

One candidate per task: temperature 0.2, top_p 1, repeat penalty 1, context 4096, generation limit 1024, fixed task-derived seed. Exact prompts are in [generation_requests.json](retained_utility_20261006/generation_requests.json). There were **44 physical local inference calls**, no retries, no paid/external calls, no learning or feedback. Each logical arm received the same one-generation budget and **identical candidate bytes**, removing model sampling noise from this post-generation retained-state contrast. This does not test learned prompting or routing channels.

The [generation manifest](retained_utility_20261006/generation_manifest.json) pins every response and confirms requests matched the freeze. Generated source was only mechanically extracted from a single fenced block if present, otherwise retained as text; no semantic repairs were made. All 44 parsed syntactically, although 19 failed correctness.

Both arms ran unchanged `echo_adapter.consult_file`, runtime, matcher and schemas. Each child initialized only isolated module copies; it did not initialize live Echo. The only instrumentation setting redirected application logs into disposable scratch, captured before cleanup. Skill A was available only in the retained root. The empty-store control still ran the enabled active consumer. A fresh process per consultation prevented cached skill objects leaking between conditions.

Task order was frozen and consumer/evaluation order alternated between conditions. E0.1 received neutral task/slot metadata and identical inputs; its scoring did not branch on arm identity. Expected answers and telemetry were inaccessible to candidates. Candidate execution used the qualified confined profile and ten-second case timeout.

## Outcomes, harms and attribution

Full [machine-readable analysis](retained_utility_20261006/out/baseline_analysis.json), [per-task telemetry](retained_utility_20261006/out/paired_telemetry.json), [paired raw records](retained_utility_20261006/out/baseline/) and per-event journals under [room_x4](retained_utility_20261006/out/room_x4/) / [room_q9](retained_utility_20261006/out/room_q9/) support independent reconstruction.

| Measure | No retained state | Retained state |
|---|---:|---:|
| Correct tasks | 25 | 25 |
| Incorrect tasks | 19 | 19 |
| Correct test cases | 760 | 760 |
| Incorrect-value cases | 232 | 232 |
| Candidate-error cases | 64 | 64 |
| Timeouts / malformed / infrastructure failures | 0 | 0 |
| Function consultations | 44 | 44 |
| Actual skill applications | 0 | 0 |
| No-match tasks | 44 | 44 |
| Correct noninterventions | 25 | 25 |

All retained consultations list A in `candidates_checked`; all control stores list no active keys. The treatment did not silently run disabled. There were no harmful interventions to hide, no useful interventions to credit, no safety rejections surfaced in task outcomes, and no selective exclusions. Broader production F1/F2 behavior was not separately benchmarked; this is the unchanged VSL-consumption seam followed by independent E0.1 correctness evaluation.

The 19 incorrect noninterventions are **not automatically 19 missed beneficial repairs**. The experiment did not establish that A could safely fix them. Representative existing failures include misspelled supplied K1 tokens, wrong return shape, reversed score selection and comparator/key API misuse. Those errors are visible in the raw code and oracle outcomes; no repair was attempted.

One non-use mechanism is specifically localized by [post-hoc static inspection](retained_utility_20261006/out/nonuse_localization.json), with **zero new candidate executions or transformations**. Item 21, `winner_from_text`, contains:

```python
ranked_entries.sort(key=lambda x: (-x[1], -tag_priority[x[2]], x[0]))
```

Its map assigns 1 to the highest-priority tag. Frozen TEST case 1 expects `ivy` (tag `nezob`) but returns `amy` (tag `kojon`) at equal top score. The local AST expression matches A's stored precondition, but the actual enclosing call is **`sort`**, whereas A requires **`sorted`**. The consumer declines. This demonstrates a specific recognition boundary on a naturally generated failing case. It does **not** demonstrate that broadening that boundary is safe or that the unchanged repair would fully correct the task; that counterfactual was not executed.

## Cost and uncertainty

Generation consumed **527.994 seconds**, **7,494 prompt tokens** and **4,397 output tokens**. This common cost is charged equally to both logical conditions. Reusing identical generation avoids spending twice without claiming a treatment efficiency gain.

| Measured runtime | Control | Retained |
|---|---:|---:|
| 44 isolated consumer calls | 2.446 s | 2.418 s |
| Median consumer call | 53.58 ms | 54.01 ms |
| 1,056 evaluator calls including recording | 34.333 s | 33.222 s |

Small timing differences are process/cache/scheduling noise, not evidence that retained knowledge accelerates work. These costs include research isolation and durable journaling; they are not production latency estimates. Extra inference due to retained state: **0**. No dollar conversion was invented.

Observed task effect: **0 percentage points**. There are no discordant pairs, so the preregistered discordance test has no informative wins/losses to evaluate. The protocol required evidence excluding a ±5-point difference for a neutral disposition; absence of a significant difference was insufficient. Even an optimistic independent-task, zero-discordance calculation permits approximately **6.6%** discordance at a one-sided 95% upper bound. Shared worlds/families further limit generalization. That calculation is an illustration of inadequate equivalence resolution, not a population confidence claim for this census.

The result therefore supports an exact statement about these observed tasks—**A added no correctness benefit and caused no correctness harm**—but does not support general positive, negative or neutral utility. It also does not quantify missed safe reuse.

## Defect-gated reuse and next decision

[The recorded gating disposition](retained_utility_20261006/out/gating_disposition.json) follows the predeclared rule: actual baseline applications = 0, trigger unmet, C not executed. No extra tasks, new skills, matching-threshold changes or altered prompts were introduced to rescue the test. The third-arm hypothesis remains untested, not falsified.

If retained A vanished on this workload, **no demonstrated correct outcome would disappear and no demonstrated harm would disappear**. Earlier selected causal transfers remain valid within their original boundaries. This result does not justify retiring A as intrinsically useless, promoting B, broadening A's authority, or reopening broad acquisition.

The smallest useful follow-up is to qualify whether the naturally observed `sort`/`sorted` recognition boundary can be handled **without authorizing harmful repairs**, using a new frozen protocol with independent defect and compatibility evidence. The specimen is a diagnostic lead, not permission to replace the net-utility workload with favorable cases. Only a separately qualified change should face another independently selected workload. Do not add more learned skills merely to avoid examining the availability-to-use failure.

## Closing integrity and deviations

[Closing integrity](retained_utility_20261006/out/closing_integrity.json), October 7 at 10:38:23 PDT: **262/262 historical authority pins unchanged**, including all original 203; every frozen protocol/input, generated candidate and pinned analysis source unchanged; staging empty and HEAD unchanged. [Closing process evidence](retained_utility_20261006/out/closing_processes.json) retains Echo PID 55361, watchdog 56610 and Ollama 1991 with their original start times.

FAISS, memory metadata, RiverBrain, self-model and runtime temporary self-edit bytes evolved while live Echo ran. They were prospectively excluded from experimental input. Hash changes alone do not establish writer attribution. No research action wrote production state, changed services, modified a skill, altered routing, used a relay, staged, committed, pushed, reset or cleaned unrelated files.

Additions are confined to this report/checksum and `audits/retained_utility_20261006/`; the namespace reflects the start date. Disposable scratch was normally cleaned under the qualified guard; expected old-guard failure fixtures remain as evidence. No inference or scoring retries occurred. A read-only model-metadata request initially failed under Codex's network sandbox and succeeded with approval; it was not an inference call. No experimental-protocol deviations were used to reinterpret outcomes.

**Did past learning make future Echo better here? No observed advantage in the tested VSL channel and workload.** Whether appropriate reuse of retained experience can provide positive net utility remains unresolved. **Did defect gating improve reuse? Not measured: no reuse occurred to gate.** Acquisition/accumulation claims should remain paused until useful, appropriately authorized reuse has demonstrated net value.

INCONCLUSIVE
