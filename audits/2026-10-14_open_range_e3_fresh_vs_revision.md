**Open Range E3 — fresh construction versus defective-code revision**

**Executive verdict: Both fail. Fresh construction nevertheless produces substantially more correct behavior.**

With complete correct facts, fresh construction passed **22/24 checks in both seeds**; revision passed **12/24 in both seeds**. No program achieved a complete verified correction. Fresh construction implemented all six mappings. Revision retained two incorrect mappings from the supplied defective source. Every program incorrectly removed categories whose aggregate was zero, despite explicit instructions to preserve them when they occurred.

Thus the failure extends beyond revision alone. The most precisely localized common defect is **confusing category occurrence with a nonzero aggregate**. The additional mapping mistakes in R support a revision-specific obstacle under this prompt arrangement, potentially source anchoring; they do not prove an internal psychological mechanism.

No stronger model was tested. The conditional installed-model inventory found no candidate satisfying the frozen stronger-model and resource criteria. Execution stopped after **4 model requests, 19 candidate launches and 50.264 seconds**. No retention, learning or production changes were made.

**Frozen comparison**

[The single protocol](open_range_e3_20261014/protocol.json) froze October 14 at 13:36:44 PDT. Execution ran 13:45:13–13:46:03. Protocol SHA-256:

`887d4f4776bc3bc8bc9996d3bda83707a4640ac13f419e3783771689c74e60e5`

The [controller](../app/experiments/open_range_e3/run.py) reuses E2's request capture, parser and checkpoints, plus the unchanged E0.1 evaluator, durable observer, batch adapter, operation-aware guard and OS confinement. It adds only F/R construction, bounded conditional inventory and scoring. Two trusted-logic tests passed before freeze, verifying matched information and hard limits.

The historical specification, eight permitted diagnostic observations, sixteen historical withheld cases, defective source and E2 trusted facts were reused unchanged. The facts were checked against all eight diagnostics using E2's trusted derivation. Hidden cases and answers stayed outside model requests. This is a historical capability diagnostic, not prospective transfer or an independently selected net-utility workload.

Both conditions received identical specification, pretty sorted-key serialization of the complete fact record, provenance description and explicit requirements: include occurring categories even at zero total; sum signed integer amounts; return `{}` for empty input; do not mutate inputs. F received no program or previous failure. R additionally received the historical defective source. The unavoidable instruction difference was “Construct…” versus “Revise the supplied defective implementation…”. The causal contrast is that bundle; it does not isolate code exposure from revision wording.

Paired seeds were 2026101431 and 2026101432. Order was F→R then R→F, with room assignments counterbalanced. All four programs were sealed before evaluation. No evaluation result entered a later inference request. Each condition had one request per seed with the same numerical settings and 1600-token generation allowance. No prompt was revised after outcomes.

Model: `qwen2.5-coder:7b`,7.6B,Q4_K_M. Manifest SHA-256 `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`; weight SHA-256 `60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463`, verified during preparation. Temperature 0.2, top-p 1, repeat penalty 1, context 8192, num_predict 1600; stateless sequential local requests. No downloads, installations or routing changes.

**Results — DIRECTLY VERIFIED**

| Model | Condition | Seed | Source status | Diagnostic | Withheld | Total | Complete correction |
|---|---|---:|---|---:|---:|---:|---|
| qwen2.5-coder:7b | F, fresh | 2026101431 | Parsed/executed; differs from baseline | 7/8 | 15/16 | 22/24 | No |
| qwen2.5-coder:7b | R, revision | 2026101431 | Parsed/executed; materially changed | 5/8 | 7/16 | 12/24 | No |
| qwen2.5-coder:7b | R, revision | 2026101432 | Parsed/executed; materially changed | 5/8 | 7/16 | 12/24 | No |
| qwen2.5-coder:7b | F, fresh | 2026101432 | Parsed/executed; differs from baseline | 7/8 | 15/16 | 22/24 | No |

All observed input lists/records remained unchanged. All proposals parsed and executed normally. Mapping singleton evidence was 6/6 for F and 4/6 for R. Exact output-key sets matched 22/24 for F and 17/24 for R. Signed arithmetic was performed, but this does not rescue incorrect mappings or key selection. The full behavioral contract was not satisfied by any program. The baseline remained 0/24, so a zero-regression count would not establish preservation of previously correct full-output behavior. No successful-candidate replay was triggered.

The source and runtime evidence agree:

- F used the correct six-code mapping, but returned only dictionary entries satisfying `total != 0` or `v != 0`.
- R corrected `favar` to `hold`, but retained `tokig → hold` instead of `closed` and `tosev → closed` instead of `open`. It also filtered with `v != 0`.
- F failed exactly diagnostic index 7 and combined case index14 (zero-based), returning `{}` instead of `{'closed': 0, 'hold': 0}`. One case involved cancellation; the other involved zero amounts. Presence and nonzero sum are different properties.

Both R source hashes are `670db14e7df0c17ef0be3df73b5b90782d2c4bfdcd0d7b5fba2a4cf35f1b6cf0`. F source hashes are `7b687088352f168a29227728d17de51812f4f221a411a562f84b70992063bed2` and `3f9d8ee4fbeb594ca706d0620faafff2b2c7532db5514049b37da627e882370d`. Raw source and complete observations are in the [evidence directory](open_range_e3_20261014/out/); [analysis.json](open_range_e3_20261014/analysis.json) reconciles scores, information matching and costs.

**Interpretation and relation to E2**

**SUPPORTED INFERENCE:** correct facts can become a correct mapping and mostly correct executable behavior in this model. Exposing the defective program plus revision wording was associated with additional mapping errors in both paired trials. Avoiding that bundle improved observed behavior, but did not produce a complete repair. Two seeds on one historical task are descriptive evidence, not a reliability estimate or proof of general superiority.

E3 changes the interpretation of E2's single oracle-assisted failure. E2 returned unchanged code at 0/24; E3 R changed code and reached 12/24, while F reached 22/24. Universal inability to implement trusted facts is therefore too strong an explanation. E3 used consistent pretty fact serialization, a shared provenance description, explicit behavioral requirements and different instructions. These changes were held constant within E3, but not individually isolated against E2. Their separate effects remain **UNRESOLVED**; no additional formatting/provenance experiments were run.

The key-rule failure is directly visible in executable source and observed outputs. Whether it reflects a model capability limit, a strong generation prior, instruction salience or another interaction remains unresolved. It is not evidence about persistent learning, acquired experience, or Echo's overall developmental potential.

**Conditional model comparison**

Only after all four primary trials failed complete correction, the controller read local `/api/tags` and `/api/ps`. [conditional_inventory.json](open_range_e3_20261014/out/conditional_inventory.json) preserves the result. The frozen selection allowed an installed Qwen2.5-Coder or Qwen3 alternative above 7.6B and at most 15B, Q4/Q5 and at most 10GiB artifact size, with sampled available memory at least artifact size+4GiB and sufficient time remaining.

No such model was installed. Available alternatives included general 8B Llama/Echo variants, DeepSeek-R1:7b, Mistral 7.2B and smaller models; this is not evidence that they are incapable or inferior. None supplied the predeclared stronger coding comparison. Sampled free+inactive+speculative memory was approximately 3.84 GiB; Qwen7B, Llama3.2:3b and Echo were resident. That snapshot also did not support loading another roughly 5 GB artifact under the conservative reserve rule. No resident model was intentionally unloaded and no service was restarted. Hardware inadequacy was not demonstrated; the conditional comparison was skipped, not failed.

**Resource accounting**

| Condition | Requests | Prompt tokens | Completion tokens | Request latency | Reported load time |
|---|---:|---:|---:|---:|---:|
| F | 2 | 1,316 | 286 | 15.777 s | 1.810 s |
| R | 2 | 1,618 | 282 | 12.354 s | 0.013 s |
| Total | **4** | **2,934** | **568** | **28.131 s** | **1.823 s** |

Loading time is the local service's `load_duration` counter and is already included in request latency; it must not be added again. Shared service activity/cache state limits latency interpretation. These are local Ollama token counts, not Codex usage.

**19 candidate launches =14 qualification controls+1 baseline+4 proposals.** Controller runtime was 50.264 seconds, including qualification, inference, scoring and conditional inventory. Two intentional timeout controls passed; no task candidate timed out. No response reached its generation-token limit. Unused allowance was left unused: hard caps were 8 requests, 24 launches and 900 seconds. There were no retries or post-result prompt changes.

**Integrity and reproducibility**

All **1,587 pinned files remained unchanged**, including prior E2/feedback evidence, relevant production source/skill authorities and the new frozen inputs. Both fresh room paths passed positive own-root reads, denied protected/history/opposite-room/hidden-answer access, denied production/surrogate writes and symlink/relative-path escapes, and passed evaluator correctness/type/exception/mutation/timeout controls. The controller write probe was denied. No qualification or integrity control failed.

The inherited limits remain: the trusted controller uses a write guard; candidate containment is OS-enforced. The batch adapter measures bounded observations and does not prove arbitrary Python correctness or immunity to all malicious observation tampering. Those limits were not weakened.

Echo PID 6316, Ollama PID 1991, Studio PID 6048, parent shell PID 5713 and tracker PID 6318 retained their observed start times. No services were signaled or restarted. Live mutable memory/state was excluded from experimental inputs and writes; independent evolution is not claimed globally byte-stable. Branch/HEAD and empty staging were preserved, along with existing tracked modifications and untracked files. No production behavior, VSL, RiverBrain or retention architecture was modified; nothing was committed, pushed or deployed.

Mission additions are `app/experiments/open_range_e3/`, `audits/open_range_e3_20261014/`, this report and its checksum. [closing_repository.json](open_range_e3_20261014/closing_repository.json) records final checks; [delivery_manifest.json](open_range_e3_20261014/delivery_manifest.json) inventories exact files/hashes. The [README](../app/experiments/open_range_e3/README.md) contains commands. Use a fresh output path for separately authorized reproduction. Requests, responses, sealed proposals, fact bytes, source hashes, per-child launch/return/comparison events and the hash-chained journal are preserved. The checkpoint marks the run complete; do not restart it.

**One recommended next action:** authorize a narrowly bounded **fresh-construction diagnostic focused on preserving occurring categories with zero totals**. It targets the only remaining F failure, while avoiding the additional revision-associated mapping errors. This is a proposed follow-up, not a code repair or experiment performed here. E3 is complete; no further inference or implementation follows from this report.
