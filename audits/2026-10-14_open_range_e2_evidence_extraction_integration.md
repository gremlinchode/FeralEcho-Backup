**Open Range E2 — evidence extraction and executable integration**

**Verdict: extraction failed; integration followed incorrect records, but correct facts did not produce a verified repair. No complete correction or task-level decomposition advantage was demonstrated.**

Both extraction trials recovered **4/6 mappings**, selected the wrong output-key rule, and cited mostly unsupported evidence IDs. Both subsequent programs faithfully implemented those incorrect records on all 24 observed inputs. They changed one mapping and passed **1/24 task checks**, versus **0/24** for direct correction. The single authorized oracle-assisted integration check received correct facts but returned the unchanged defective program, passing **0/24**.

The earliest demonstrated failure is **evidence extraction**. It is not established as the sole bottleneck: one integration attempt also failed with a complete correct record. The experiment is closed after **9 model requests, 22 candidate launches and 116.17 seconds of controller execution**. No unused budget was spent on retries.

**Frozen design and controls**

The implementation is [open_range_e2/run.py](../app/experiments/open_range_e2/run.py); evidence is under [open_range_e2_20261014](open_range_e2_20261014/). The single [protocol](open_range_e2_20261014/protocol.json) froze at 08:58:10 PDT, before execution from 09:02:23 to 09:04:19. SHA-256:

`ac74e6b4be6437a950b4bb33cad0918b0066cd1bcc0c845addbf0c9ef98a8d0c`

We reused the original historical `categorize(records)` task, defective source, eight diagnostic observations and sixteen historical withheld cases. This is a diagnostic on previously exposed evidence, not fresh transfer. Each of six nonzero singleton observations uniquely identifies one status/category relationship under the task specification. Empty input and the cancellation/zero observation establish output-key behavior. The trusted fact oracle was derived from these permitted observations, checked against all eight, and independently compared with the previously frozen world mapping in a preflight unit test. It did not use hidden answers to extract facts. Evidence was sufficient; no missing relationship was invented.

Model remained `qwen2.5-coder:7b`, 7.6B, Q4_K_M. Manifest SHA-256 `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`; weight SHA-256 `60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463`. We verified the weight during preparation. Decoding remained temperature 0.2, top-p 1, repeat penalty 1, context 8,192 and maximum 1,600 generated tokens per request. Calls were sequential and stateless; no model substitution or production routing change occurred.

- **A, direct:** specification, defective source and eight diagnostic observations; code-only response. Two independent proposals per seed, selected by diagnostic score, earliest tie. No separate fact record or hidden feedback.
- **B, extraction:** same specification and observations, without initial source; a small JSON schema for bindings, evidence IDs, key policy, amount aggregation, input mutation, uncertainty and contradiction. No executable code requested. Facts were scored privately before C.
- **C, integration:** specification, defective source and B's **exact raw response string**, without investigator correction or B's score. No original diagnostic or hidden answers were added to C.
- **O, conditional oracle-assisted integration:** one call after B failed, using facts derived by the trusted controller from permitted diagnostics. Explicitly labeled as oracle-assisted; no replacement Python source supplied. Its score is separate from the A versus B+C comparison.

Seeds were `2026101411` and `2026101421`. A1/B used the base seed; A2/C used base+1. Order was A1,A2,B,C for the first pair and B,C,A1,A2 for the second; room assignments swapped. O used the first failing seed+1. Each compared path had **two requests and 3,200 generated-token allowance per seed**. A used both calls for code search; B+C spent one on extraction. Both had capacity for two distinct candidate evaluations, although C used one. Actual costs are reported below.

All code proposals were sealed before executable evaluation. Direct selection used only the eight diagnostic scores even though evaluation returned all observations in one confined batch. Hidden results never entered any subsequent model request. B's schema and the staged prompts are investigator-engineered elicitation; they are not evidence of autonomously acquired representation design.

**Results**

`—` means not applicable. Mapping score alone is insufficient for extraction success. Neither B record passed complete extraction. A1 was selected in both pairs because both direct proposals tied at zero diagnostic correctness.

| Condition | Seed | Extraction | Source changed | Diagnostic | Withheld | Verified correction |
|---|---:|---|---|---:|---:|---|
| A1 direct, selected | 2026101411 | — | No | 0/8 | 0/16 | No |
| A2 direct | 2026101412 | — | No | 0/8 | 0/16 | No |
| B extraction | 2026101411 | 4/6 mappings; key rule wrong | — | — | — | — |
| C own-fact integration | 2026101412 | Uses failed B record | Yes | 0/8 | 1/16 | No |
| B extraction | 2026101421 | 4/6 mappings; key rule wrong | — | — | — | — |
| C own-fact integration | 2026101422 | Uses failed B record | Yes | 0/8 | 1/16 | No |
| A1 direct, selected | 2026101421 | — | No | 0/8 | 0/16 | No |
| A2 direct | 2026101422 | — | No | 0/8 | 0/16 | No |
| O oracle-assisted integration | 2026101412 | Trusted complete correct record | No | 0/8 | 0/16 | No |

Machine-readable rows use the pair's base seed and a stage label; exact request seeds are in each `*_request.json`. [analysis.json](open_range_e2_20261014/analysis.json) reconciles all rows, counts and raw-record forwarding.

Both B records asserted `favar → open` instead of `hold`, and `tokig → hold` instead of `closed`. They correctly assigned the other four codes. Both chose `ALL_CATEGORIES` instead of `OCCURRING_CATEGORIES`, despite the specification and empty-input counterexample. Signed summation and no mutation were correctly represented. Only one binding's citation list passed the frozen ID-relevance rule; its category was still wrong. The raw field named `evidence_supported` checks citation linkage, while category correctness is scored separately. Unrelated observations were attached to other bindings. The second record additionally described record IDs 31 and 33 as uncertain category codes. These IDs were not status codes. The first record listed generic `UNKNOWN`. These are direct evidence of incomplete extraction and role confusion, not just bad Python generation.

Both C programs changed `tosev` from `closed` to `open`, exactly matching the model's record, but retained the record's other mapping mistakes and all-category output. Source SHA-256:

`502c7344719c0f0ab437320764e28dc22d42d4443f5f194005b1bc94f1866940`

For each C output, the trusted controller separately computed expected behavior **under that incorrect record** and compared it with the already-observed results. This narrow record-fidelity score was **24/24**. It did not certify the record as true. The only task-correct withheld case contained neither misclassified code and included all three categories; it also benefited from the corrected `tosev` assignment. It was the same case in both seeds, not two independent transfer examples.

O received the complete correct mapping, occurring-key rule, signed-sum rule and no-mutation requirement, yet returned the original source hash:

`aba7d083d7bc12e9a3ca405b30eb07c96b8e4fce50fd41486783590f5246b41c`

It matched the correct record on **0/24** observations. Correct facts therefore did not rescue this particular integration attempt. This single diagnostic does not prove a universal inability to implement correct records. O used a labeled trusted record with compact serialization; C used exact model-produced formatting. Content, provenance label and record formatting differ. Their individual contributions are unresolved, and the frozen experiment permits no additional tuning.

**Failure localization and interpretation**

**DIRECTLY VERIFIED:** wrong factual relationships and the wrong key rule appear in B before code generation. C can turn its record into corresponding code and observable behavior. O fails even when extraction is bypassed with correct facts. All seven code proposals parsed and executed; no parser fallback, candidate-selection loss or sandbox failure explains the outcomes. All responses stopped normally rather than reaching the generation cap.

**SUPPORTED INFERENCE:** extraction is the earliest repeatable blocker, and executable integration is not reliable independently of record content/presentation. The results reject an account in which every failure is simply inability to make any source change. They also reject treating successful record following as successful task repair.

**UNRESOLVED:** why expected diagnostic facts lose to incorrect inferred relationships; whether initial-source anchoring, evidence-role confusion, record presentation or another model/interface interaction causes O's failure. We did not observe internal model reasoning or server prompt rendering. No stronger model or alternative prompt was tested after outcomes.

Task-level paired outcomes are two ties at failure: **zero decomposition wins and zero direct wins**. Decomposition improves one of 24 observed cases per seed, which is a real partial correction, but it does not meet the frozen complete-repair criterion. The original baseline passed no complete input/output checks, so zero observed regressions is vacuous; there was no previously correct full-output cohort to preserve. No successful-code replay was triggered. Two seeds on one historical task do not support a population or generalization estimate.

**Resource accounting**

| Path | Requests | Prompt tokens | Completion tokens | Request latency |
|---|---:|---:|---:|---:|
| A direct, both seeds | 4 | 3,700 | 500 | 37.27 s |
| B+C, both seeds | 4 | 3,169 | 776 | 49.90 s |
| O, separate diagnostic | 1 | 644 | 125 | 5.97 s |
| Total | **9** | **7,513** | **1,401** | **93.15 s** |

Controller execution totaled **116.17 seconds**, including qualification and evaluation. Candidate launches reconcile to **14 qualification controls + 1 baseline + 4 direct programs + 2 own-record integrations + 1 oracle-assisted integration = 22**. No model or candidate retries occurred. Two intentional timeout controls behaved as expected; no task candidate timed out. The lowest sampled free+inactive+speculative memory estimate was about 3.62 GiB; monitoring is not a hard allocation limit. The live model service was shared, so latency differences are not a controlled throughput claim. The additional decomposition output/latency did not buy a complete repair.

Hard caps12 requests/30 launches/1,200 seconds were enforced by the new mission budget; historical usage was not counted as new E2 execution. The plan used fewer requests than permitted and stopped after its fixed comparisons and conditional check.

**Integrity and reproducibility**

All **1,400 pinned authorities and historical evidence files remained unchanged**. Both fresh room paths passed own-root positives, retained/history/opposite-root/hidden-answer read denial, production/surrogate write denial, symlink/relative-path controls and unchanged evaluator behavior controls. Expected answers stayed in the controller. Durable launch, comparison and return records survive cleanup. The controller's explicit production-write probe was denied; no unexpected denial occurred.

The existing E0.1 worker, independent comparison, batch adapter, operation-aware guard and OS confinement were reused unchanged. Their bounded observation limits remain: returned values/types, errors and input mutation are measured, not arbitrary Python correctness or all malicious observation tampering. No new retention mechanism was implemented.

Branch remained `vsl-implementation`, HEAD `7423d5592d8a27db6b4048147771f7b4a2585500`, staging empty. The fourteen pre-existing tracked-modification paths and pre-existing untracked files were preserved. Echo6316, Ollama1991, Studio6048, parent shell5713 and tracker6318 retained their observed start times. No services were restarted or signaled. Live mutable state was observed, excluded from inputs and not written by the experiment; independent evolution is not claimed byte-stable or attributed from snapshots alone.

Mission additions are `app/experiments/open_range_e2/`, `audits/open_range_e2_20261014/`, this report and its checksum. Exact files/hashes are in [delivery_manifest.json](open_range_e2_20261014/delivery_manifest.json); repository checks are in [closing_repository.json](open_range_e2_20261014/closing_repository.json). Nothing was staged, committed, pushed, installed or promoted.

The [README](../app/experiments/open_range_e2/README.md) provides entry points. Use a new output namespace for separately authorized reproduction; never rerun the closed directory. Five trusted-logic tests passed before freeze. Requests, raw responses, unedited fact records, private fact scores, code, source hashes, sealed proposals, per-child argv/stdin/stdout/exit/comparison evidence and the hash-chained journal are preserved under `out/`. Analysis is reproducible with `python -I -B app/experiments/open_range_e2/analyze.py --output <fresh-output>` after a fresh run; it intentionally refuses to overwrite an existing analysis.

**Exactly one recommended next action: 1. Repair evidence extraction.**

The repeated earliest defect is mistaking evidence roles and output obligations before any code is requested. A narrowly bounded follow-up should address that operation first and independently test whether every asserted mapping and key rule is supported by its cited diagnostic evidence. E2's oracle-assisted failure must remain an explicit downstream integration blocker; fixing extraction alone must not be presented as a complete solution. No follow-up is begun here.

E2 demonstrates partial record following, failed factual extraction, and an unsuccessful correct-record integration check. It does not demonstrate persistent learning, general transfer, or developmental improvement.
