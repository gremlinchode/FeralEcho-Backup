**Open Range E4 — Verified Learning and Independent Transfer**

**Executive verdict: ACQUISITION FAILED. Transfer was not run; retained-lesson utility remains unmeasured.**

The installed model generated a fresh program with correct mappings but an incorrect positive-total filter. After a minimal counterexample, both permitted corrections changed the source without changing any of the 30 observed outcomes. All three programs passed **12/30 checks**. Neither explanation identified the actual membership-versus-value defect. No lesson was designated acquired or verified, and none was supplied to a transfer request.

Execution completed within the frozen limits: **3 model requests, 19 candidate/evaluator launches, 184.135 seconds**. No isolation or integrity control failed. This is an acquisition failure under this interface and budget, not negative transfer, a retained-learning null result, or proof that the model cannot learn.

**Implementation and prospective freeze — DIRECTLY VERIFIED**

The research-only [controller](../app/experiments/open_range_e4/run.py) and [task/prompt definitions](../app/experiments/open_range_e4/design.py) reuse E2 request capture and parsing, unchanged E0.1 evaluation, durable observation, the batch adapter, operation-aware write guard and OS confinement. New code adds the bounded acquisition gate, model-authored lesson review gate, isolated retention path and matched transfer controller. Four trusted-logic unit tests passed before freeze: literal-answer/oracle agreement, prompt information separation, exact record preservation, and request/budget configuration. These tests do not execute generated programs.

[Protocol](open_range_e4_20261014/protocol.json) frozen **2026-10-14 14:16:48 PDT**, before all E4 inference:

`95dcf8148427b652a1fac56d10995c138d8cdb98905948bba3c4d9653ef8a2fb`

Hard caps were 16 requests, 48 launches, 900 seconds and two acquisition corrections. The planned maximum was 11 requests and 28 launches. The deadline spans acquisition, independent review and transfer; counters persist across controller processes. Calls are charged before attempts, with bounded request/child timeouts and an absolute controller alarm. Failed launches count. No prompt, test, threshold or frozen implementation was changed after execution began.

**Acquisition specification and independence**

The initial request supplied the historical task specification and its six established mapping facts. It supplied neither prior source nor E3 scores, the trusted output-key fact record, an explicit zero-total lesson, or a replacement implementation. The mapping facts are current-task information, **not knowledge acquired in E4**. This deliberately avoids repeating the already demonstrated mapping-extraction difficulty.

The specification still requires exactly the categories occurring in the input and prohibits input mutation. That requirement is authoritative task information. The model was left to derive its executable implementation and, after failure, the corrective lesson.

Acceptance used the unchanged eight historical diagnostics and sixteen historical withheld cases, plus six frozen acquisition checks: one explicit-zero and one cancellation check for each category. These 30 literal expectations were independently cross-checked by trusted grouping logic. The sixteen historical withheld answers remained outside model requests. They are historical evaluation material, not new prospective transfer evidence.

The feedback allowance was the first failing added zero/cancellation case in frozen order. Both corrections received the same single case:

```json
{"input":[{"id":401,"status":"favar","amount":0}],
 "expected":{"hold":0},"observed":{}}
```

The actual request also records successful execution and unchanged input. It contains no other evaluation scores or hidden cases. Each correction request includes the previously submitted source and asks for an explanation, lesson, applicability, uncertainty and complete revised source. The response schema specifies fields, not the desired lesson or repair.

A correction would need all 30 checks, source change, fresh-child replay and an independent review of its unedited model-authored lesson before transfer. Review would check explanation fidelity, occurrence/value distinction, appropriate scope, absence of invented authority and reusability. Because executable verification failed, neither replay nor lesson approval was reached.

**Observed acquisition results — DIRECTLY VERIFIED**

| Proposal | Seed | Source change from initial | Historical diagnostics | Historical withheld | Added zero/cancellation | Complete correction |
|---|---:|---|---:|---:|---:|---|
| Fresh construction | 2026101441 | New source | 7/8 | 5/16 | 0/6 | No: 12/30 |
| Correction 1 | 2026101442 | AST changed | 7/8 | 5/16 | 0/6 | No: 12/30 |
| Correction 2 | 2026101443 | AST changed | 7/8 | 5/16 | 0/6 | No: 12/30 |

All three parsed and executed normally, implemented all six mappings and preserved observed inputs. All 30 returned observations were identical across attempts. **Fixes: 0. Regressions relative to the fresh candidate: 0.** Source change alone therefore gave no behavioral improvement. Empty input passed; all eight cases containing expected zero-valued category totals failed. The negative-total cases exposed additional failures.

The fresh source ends with:

```python
return {k: v for k, v in result.items() if v > 0}
```

Correction 1 incorrectly blamed the ordering of category checks and moved `hold` before `open` and `closed`. The code already had a branch for `hold`, and the status sets are disjoint. It retained the positive-total filter. Its explanation explicitly claimed no uncertainty.

Correction 2 incorrectly blamed unmapped statuses and added an `else: pass`. The supplied failing status, `favar`, is explicitly mapped to `hold`; the task's valid codes are all mapped. It again retained the filter and claimed the issue had been identified. The resulting narrative is not supported by its executable behavior.

Source SHA-256 values, in order:

```text
0dd921dbe034e6872c96378f4f48d54f0e1679928511873780ee9314cf3157b1
ff0728d30aa34268b1304fda626958184e7e68ecf95020ff19324d5cd6c827d5
09861539f3c21e498ec244f4c7be0215cc1482ca89da68203495c8a57971fc78
```

Raw [requests, responses, sealed proposals and scores](open_range_e4_20261014/out/) preserve both failed explanations unchanged. [analysis.json](open_range_e4_20261014/analysis.json) reconciles outcomes, costs, request construction and journal counts.

**Failure boundary and relation to E3**

**SUPPORTED INFERENCE:** the observed bottleneck is translating the counterexample into an accurate defect explanation and a consequential correction. Both edits addressed unsupported explanations while leaving the actual output filter intact. Corrective text and source changes were transmitted and evaluated; no successful correction was discarded by selection or parsing.

E4 is not an exact replication of E3. E3 fresh programs filtered with `!= 0` and passed 22/24; this fresh request used a simpler mapping presentation and omitted the explicit zero-preservation requirement beyond the historical contract. Its program used `> 0`, also excluding negative totals. Cross-mission scores do not isolate the cause of that difference. The frozen E4 gate required a demonstrated zero-total failure and correct singleton mappings; it did not require that zero totals be the sole failing behavior. Full acceptance still required every case to pass.

**UNRESOLVED:** whether a different corrective interface would enable a verified correction, whether prior-source exposure contributes to this failure, and the model's broader capability. There was no feedback-free correction control, but no correction succeeded from which to claim feedback causation. Confident incorrect explanations are observations; an internal cognitive mechanism is not established.

**Independent transfer design — FROZEN, NOT EXECUTED**

Four fresh task specifications and all 32 answers were fixed before acquisition: inventory deltas by SKU, credit-minus-debit totals by account, nested station adjustments, and cross-batch measurements returned as sorted label/total pairs. They include cancellation, explicit zero, absent entities, nonzero totals, empty inputs and distinct empty-inner-container semantics. No historical six-code mapping is required. Literal answers agree with a separate trusted grouping oracle.

These are investigator-authored targeted transfer tasks, independent of the observed E4 outputs. They are not an independently sampled population or independently held case-custody exercise. Any favorable result would have supported only this bounded related-task comparison.

The frozen R/C pipeline uses one paired seed per task (2026101444–2026101447), counterbalanced request order and room assignment, identical stateless templates apart from the exact retained lesson/applicability versus null, and equal inference settings. All eight sources must seal before transfer scoring. Primary endpoint: tasks passing their complete eight-check contracts. Secondary endpoints include zero preservation, key sets, arithmetic, empty behavior, mutation, exceptions, tokens and latency.

**No verified lesson artifact was created. No retrieval, transfer inference, transfer candidate execution or paired comparison occurred.** Complete-task advantage, resource-adjusted transfer benefit and retention harms are **NOT TESTED**, not zero. The conditional transfer implementation remains unexecuted and unqualified end to end. No oracle-authored lesson was substituted.

**Resources and model identity — DIRECTLY VERIFIED**

Model: `qwen2.5-coder:7b`, 7.6B, Q4_K_M. Temperature 0.2; top-p 1; repeat penalty 1; context 8192; generation allowance 1600 tokens. Each request is stateless and sequential. All responses ended normally, below the generation limit.

Manifest SHA-256: `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.

Weight SHA-256: `60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463`, checked before and after execution.

| Stage | Requests | Prompt tokens | Completion tokens | Request latency |
|---|---:|---:|---:|---:|
| Fresh construction | 1 | 306 | 169 | 24.114 s |
| Correction 1 | 1 | 628 | 508 | 68.526 s |
| Correction 2 | 1 | 628 | 458 | 67.348 s |
| Total | **3** | **1,562** | **1,135** | **159.988 s** |

Reported model load time was 3.321 seconds, already included in request latency. These are local Ollama counters, not Codex token usage. No additional model was loaded by this mission.

**19 launches =16 qualification controls +3 acquisition candidates.** Qualification included both-room filesystem controls, correct/incorrect/type/exception/mutation/timeout controls and structured zero-output checks. Two intentional timeout controls passed; acquisition candidates did not time out. Controller execution ran **14:17:04–14:20:08 PDT**, taking **184.135 seconds**, including qualification. No retry or extra experiment followed the stopping result.

Sampled available-memory estimates ranged from 2,358,493,184 to 5,236,506,624 bytes. This is a host-state estimate, not candidate peak RSS or a hard memory allocation guarantee. Energy and attributable model memory were not measured. The unsuccessful acquisition incurred cost without a verified repair or measured future benefit.

**Integrity and reproducibility — DIRECTLY VERIFIED, with live-state attribution limits**

All **1,741 pinned authority/input files** remained byte-identical, including prior E3/E2 evidence and relevant production/evaluator sources. Both rooms permitted own-root reads and denied protected skills, opposite-room files, historical answers, hidden canaries, production/surrogate writes and tested path/symlink escapes. The controller's production Skill A write-open probe was denied. Request reconstruction confirms only the declared public task data and permitted feedback entered model calls. The durable journal hash chain validates.

Branch remained `vsl-implementation`; HEAD remained `7423d5592d8a27db6b4048147771f7b4a2585500`; cached origin/main remained unchanged, with 5 ahead/0 behind and no fetch. The 14 pre-existing tracked modifications and prior untracked paths were preserved. Staging remained empty. No commits, pushes, deployments, downloads or installations occurred.

Echo PID 6316, Ollama PID 1991, Studio PID 6048, parent shell PID 5713 and tracker PID 6318 retained their observed identities/start times throughout checks. No service was signaled or restarted. Research made no production writes or changes to VSL, RiverBrain, FAISS, routing or the self-model.

Live `memory/river_brain.pkl` and `memory/self_model.json` evolved between snapshots. These qualified mutable files were excluded from experimental inputs and write authority. Their writer was not independently attributed; global production byte stability is not claimed. Immutable authority remained stable and the research write boundary remained intact.

Mission additions are limited to `app/experiments/open_range_e4/`, `audits/open_range_e4_20261014/`, this report and its checksum. [closing_repository.json](open_range_e4_20261014/closing_repository.json) and the delivery manifest record preservation and exact additions. A post-run reporting helper initially misread a repository-command result's type; only reporting extraction was corrected, with no experimental rerun or frozen-file change ([note](open_range_e4_20261014/postprocessing_note.json)).

The [README](../app/experiments/open_range_e4/README.md) provides preparation, execution and conditional review commands. Reproduction requires a fresh audit namespace and separate authorization; the completed namespace rejects reruns. The checkpoint closes this mission. The inherited evaluator measures bounded observations, not arbitrary Python correctness or every possible malicious adapter attack.

**Answers and one next action**

1. **Did bounded feedback produce an independent correction?** No. Both revisions preserved every observed outcome.
2. **Was a valid verified lesson acquired?** No. The executable gate failed, and both explanations were unsupported by the failure.
3. **Was a verified lesson preserved and retrieved later?** No. Failed raw records were preserved as evidence only.
4. **Did retention outperform control on independent tasks?** Not tested; acquisition failure prevented the comparison.
5. **Did an advantage survive complete-contract evaluation?** No advantage was measured; no acquisition program satisfied its complete acceptance suite.
6. **What did it cost?** 3 requests, 1,562 prompt tokens, 1,135 completion tokens, 19 launches and 184.135 controller seconds.
7. **What remains unproven?** Verified acquisition of this lesson, later beneficial reuse, persistence and any improvement to production Echo.
8. **Single recommended next action:** a bounded paired acquisition test comparing **fresh reconstruction from the same counterexample without defective source** against revision with that source, using the same mapping facts and acceptance suite. E3 supplies a reason to test source exposure, while E4 shows ineffective edits to retained faulty code. This would test a narrow acquisition route, not establish an anchoring mechanism or authorize further retention engineering. It was not performed here.

**Final disposition: ACQUISITION FAILED. E4 execution is closed.**
