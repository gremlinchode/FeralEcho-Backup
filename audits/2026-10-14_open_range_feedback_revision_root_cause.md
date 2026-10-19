**Open Range — feedback-to-revision investigation, October 14, 2026**

**Verdict: VERIFIED CORRECTION DEMONSTRATED; ORIGINAL-TASK FAILURE LOCALIZED, NOT FULLY EXPLAINED.**

The installed `qwen2.5-coder:7b` can revise a demonstrated mistake and produce independently verified executable behavior. All six feedback-present trials on the fresh consecutive-runs task passed every diagnostic, regression and withheld check. The same historical Open Range interface worked on that task. However, five of six matched no-counterexample controls also succeeded. Only one matched pair favored feedback; this is limited descriptive evidence of feedback benefit, not a reliable estimated causal effect.

The original convention-learning failure remained. All six historical confirmation trials failed, including direct code-only correction and explicitly corrective instructions. A separately frozen presentation probe also failed: changing the direct request from JSON to labeled plain text did not change the incorrect program. We used all **24 authorized model requests**, **58/60 candidate launches**, and **791.77/3,600 controller seconds**. Experimental execution is closed. No stronger model was tested because the stipulated trigger—failure of both direct and clarified correction on the primary diagnostic—did not occur.

The twelve original revisions failed **before parsing or candidate selection**: their raw service responses already contained unchanged code. The new evidence contradicts a general inability to correct code and a universal obstruction in the old controller interface. It does not distinguish a task-specific model limitation from the remaining interactions between prior-code anchoring, fact extraction, instruction interpretation and local-service behavior. No retained-learning or persistent competence claim follows.

Evidence labels below distinguish **DIRECTLY VERIFIED** source/runtime facts, **SUPPORTED INFERENCE**, and **UNRESOLVED** mechanisms. The full raw evidence is under [feedback_revision_20261014](feedback_revision_20261014/); [final_analysis.json](feedback_revision_20261014/final_analysis.json) reconciles counts, source transport and every outcome.

**1. Preservation and implementation**

Opening state was recorded at 03:45:08 PDT: branch `vsl-implementation`, HEAD `7423d5592d8a27db6b4048147771f7b4a2585500`, cached `origin/main` `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, ahead/behind 5/0 without fetching, empty staging, and fourteen pre-existing tracked modifications. The detailed inventory is [opening.json](feedback_revision_20261014/opening.json). Existing modified and untracked work was preserved.

Only additive diagnostic software and evidence were created. [diagnostic.py](../app/experiments/feedback_revision/diagnostic.py) builds immutable requests, captures service bytes, parses without code substitution, seals proposals, then evaluates them. [presentation_probe.py](../app/experiments/feedback_revision/presentation_probe.py) performs the separately frozen follow-up with cumulative budgets. `analyze.py` and `summarize.py` read results; neither executes candidate text or calls a model. The six primary unit tests and two presentation tests cover oracle expectations, matched request construction, absence of counterexamples in controls, parser behavior, material-change checks, budgets and serialization. They passed. See [unit_tests.txt](feedback_revision_20261014/unit_tests.txt) and [presentation_unit_tests.txt](feedback_revision_20261014/presentation_unit_tests.txt).

The existing Open Range batch adapter, E0.1 worker/comparison, durable observer, operation-aware controller guard and narrow OS profiles were reused unchanged. Candidate code ran only in disposable confined children. The model could submit complete source; investigators did not repair its submissions. This was an isolated research controller using Echo's installed model, not execution inside the live Echo orchestrator.

**2. Reconstruction of all twelve original failures**

[original_trace.json](feedback_revision_20261014/original_trace.json) preserves, for every original revision: the complete request, preceding source, explicit input/expected/actual feedback, raw service response, parsed source, reconstructed execution wrapper, source hashes, launch argv/stdin, child return and final selection index. [original_trace_findings.md](feedback_revision_20261014/original_trace_findings.md) records the evidence limits.

| Link | DIRECTLY VERIFIED result |
|---|---|
| Feedback construction | All twelve sent requests include the preceding program and all eight diagnostic observations, including expected and actual values. |
| Raw response | All twelve already contain the preceding source unchanged. |
| Parsing | The unchanged parser reproduces the archived proposal exactly; no corrected source was lost. |
| Evaluator input | Reconstructed batch-wrapper hashes match the historical evaluation-begin hashes. Children returned evaluable results. |
| Selection | Attempt zero wins equal validation scores. All attempts within each cycle have identical source, so selection did not discard a repair. |
| Generation limits | All end with `done_reason=stop`; 354–469 completion tokens against 1,600 allowed. Reported prompt counts are 1,482–2,762 against context 8,192. |
| Schema restrictions | Explanations have 280-character field bounds; some prose ends awkwardly. Source fields permit 2,600 characters. This is distinct from hitting the generation-token ceiling. |

For example, the historical acquisition source hash is `aba7d083d7bc12e9a3ca405b30eb07c96b8e4fce50fd41486783590f5246b41c` in both arms' revisions. Its `categorize` program assumes `favar → open`, while the supplied singleton observation requires `{'hold': 3}`. It also initializes all three category keys despite the requirement to return only occurring categories. The feedback included all six singleton mappings, empty input and cancellation/zero behavior. The missing information was available in the request; it was not converted into revised executable behavior.

**SUPPORTED INFERENCE:** the original break is at or before service response generation, rather than transport from the raw response through parsing and selection. This is a localization, not an account of the model's internal reasoning.

**UNRESOLVED:** historical scratch source was removed by normal cleanup, so execution linkage is reconstructed from hashes rather than an independent worker-side file-read hash. The installed template iterates over user/assistant messages; it has no inspected rule dropping the last turn. Neither template inspection nor API token counters expose the server's actual rendered token sequence, attention or cache correctness. They cannot prove comprehension or exclude every server-side transport defect.

**3. Frozen matched experiment**

The primary [protocol](feedback_revision_20261014/protocol.json) froze at 03:49:10 PDT, before execution at 07:04:35–07:16:45. SHA-256:

`e364995cfa34f16cffe91673aaab4e38d135acf9bca01bf05b6d3d739a531dd6`

Model: `qwen2.5-coder:7b`, 7.6B, Q4_K_M. Manifest SHA-256 `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`; weight SHA-256 `60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463`. The weight was hashed during preparation; model manifest/template and relevant files were pinned. All requests used temperature 0.2, top-p 1, repeat penalty 1, context 8,192, maximum generated tokens 1,600, sequential stateless `/api/chat`, and at most 360 seconds per request. No weights, quantization, numerical generation settings or production routing changed.

The fresh task was `count_runs(items)`: count maximal consecutive equal-value runs without mutating the list. The deliberately defective initial solution was `return len(set(items))`. The diagnostic input `[4,4,7,4]` requires 3; the initial program returns 2. Four regression cases and twelve withheld cases cover empty/singleton, repetition, separated repetition, negative values and alternating runs. Hand-listed expectations were independently checked by adjacent-boundary counting before freeze. No correct replacement source was supplied. Baseline execution confirmed 8/17 total correct, the diagnostic failure, and all four declared regression cases passing.

All conditions received the same specification and initial source. Feedback-present requests received the same counterexample; controls received no diagnostic inputs or answers. Hidden expectations never entered model requests.

| Condition | Interface |
|---|---|
| A — Direct | One user request containing task, source, initial hypothesis and feedback; complete Python response, no JSON output grammar. |
| B — Existing | Historical system/task/assistant-history arrangement, unchanged JSON schema/parser and revision instruction. |
| C — Clarified | Same B history and schema; only final instruction changes to identify the contradicted assumption, describe the required change, submit revised source and predict the first diagnostic return. |

A/B changes packaging and output format together; it does not isolate either variable alone. B/C isolates the final corrective instruction. Seeds `2026101401` and `2026101402` were paired across conditions and feedback controls; request order was frozen and counterbalanced. Every proposal was sealed before hidden evaluation. AST change alone was insufficient: diagnostic, regression and withheld checks all had to pass. No response was edited or resubmitted after scoring.

**4. Primary results and feedback attribution**

| Condition | Feedback-present verified corrections | No-counterexample verified corrections | Feedback wins / losses / ties |
|---|---:|---:|---:|
| A — Direct | 2/2 | 2/2 | 0 / 0 / 2 |
| B — Existing | 2/2 | 2/2 | 0 / 0 / 2 |
| C — Clarified | 2/2 | 1/2 | 1 / 0 / 1 |

**DIRECTLY VERIFIED:** all twelve proposals materially changed the initial program. Eleven passed 17/17 checks, fixing nine baseline failures without damaging its eight passing observations. The first feedback-present success in each interface reproduced exactly in a fresh evaluator child (three replays). These are executable corrections, not verbal claims.

The decisive differing pair is C at seed `2026101401`. With feedback, the model increments a count at each adjacent value change, predicts `3`, and passes 17/17. Its source SHA-256 is `b00297f9b20d388c8b27652d54aae34beab8e4ec0a643c8566cd87c4c1c42529`. Without feedback, it resets a count whenever the value changes and returns the final run's length; it returns `1` for the diagnostic, passes 4/17, fixes none of the initial failures and damages four previously passing observations. Both responses claim to count runs. Independent execution distinguishes the claims.

This pair supports a narrow feedback-sensitive outcome. It does **not** establish that feedback caused all six successful corrections, that C is superior to B, or that repeated seeds are independent tasks. A and B succeeded without feedback in every primary trial. There is no statistical significance claim from one fresh task and two seeds. A full task specification itself often supplied enough information to fix the initial code.

**5. Historical confirmation and presentation falsification**

The preregistered confirmation trigger was met. Six requests reused the original acquisition task, defective program and eight diagnostic cases, with the same interfaces and seed `2026101403`. Sixteen original TEST cases were excluded from requests. They are historical, previously exposed evaluation material—not new prospective transfer evidence.

| Condition | Feedback success | Control success | Material source changes |
|---|---:|---:|---:|
| A | 0/1 | 0/1 | 0/2 |
| B | 0/1 | 0/1 | 0/2 |
| C | 0/1 | 0/1 | 1/2, control only |

Every program scored 0/24. C's control changed to a different incorrect categorization scheme. C with feedback explicitly described expected `{'hold': 3}` versus observed `{'closed': 0, 'hold': 0, 'open': 3}`, but submitted the unchanged map and predicted the unchanged erroneous return. B also acknowledged mismatched expectations without changing source. This directly demonstrates a gap between noticing a contradiction in prose and implementing the needed behavior. It does not identify whether full mapping extraction, code regeneration, anchoring or another model/interface interaction is responsible.

The remaining six-request allowance was used for one additive diagnostic, [FEEDBACK-PRESENTATION-v1](feedback_revision_20261014/presentation/protocol.json). It froze at 08:38:10, then ran 08:38:29–08:39:31. SHA-256:

`048bf560a0dbd170f45d7965274df333ea1eb8a97952e8812b8b960784be8eb7`

It preserved A's code-only output interface, system message, task, initial source/hypothesis, all feedback fields and numerical settings. Only user-content serialization changed from a JSON object to labeled plain text. Seeds `2026101403` and `2026101404` supplied feedback/control pairs. The existing JSON pair at seed 1403 was reused as evidence, not executed or counted twice; two new JSON and four plain-text requests completed the matrix. The supplemental freeze pinned the completed main results, carried its counts/time, and reran all fourteen confinement/behavior controls before inference.

| Input presentation | Feedback-present success | Control success | Material changes |
|---|---:|---:|---:|
| JSON | 0/2 | 0/2 | 0/4 |
| Plain text | 0/2 | 0/2 | 0/4 |

All six new programs scored 0/24 and were AST-identical to the defective initial program. Thus the simple serialization repair did not resolve this failure. This follow-up was chosen after observing the main failure, frozen before its own outcomes, and not used to revise the main experiment. Reused comparisons span execution periods; caching, load and sampling reproducibility remain limits. No further tuning or calls were attempted.

**6. Competing explanations**

| Hypothesis | Assessment | Evidence and remaining boundary |
|---|---|---|
| H1 — Model capability | **Contradicted in general; unresolved for convention learning** | The same artifact independently fixes the fresh task, including through the historical interface. It still fails to turn explicit convention observations into correct code. A task-specific capability limit remains plausible. |
| H2 — Prompt/interface | **Unresolved overall; tested simple fixes did not rescue the historical task** | Existing B works on the primary task. Clarified C, code-only A and labeled input all fail the historical task. Explanation bounds and permission to abstain exist, but they are not established causes. |
| H3 — Controller/transport | **Contradicted for correction loss after the API response; server-internal path unresolved** | All twelve original raw responses already contain unchanged source; parser and execution hashes agree. New responses also survive parsing intact. No internal prompt-token trace was captured. |
| H4 — Interaction | **Unresolved, with task dependence directly observed** | Interface alone and a universal model incapacity do not explain both task outcomes. A model/task/prior-source interaction is plausible, but no component interaction has been uniquely identified. |

A token-budget explanation is unsupported by the observed stopping data: none of the 24 new responses hit the generation limit, and none of the twelve historical revisions did either. Field-level truncation is real and separate; it was not varied experimentally. No larger-model test was warranted under the frozen trigger. Model size, hardware scarcity and a fundamental inability to learn were not established.

**7. Retention findings — design only**

Source inspection of [core.retrieve](../app/experiments/open_range/core.py) and [Experiment.cycle](../app/experiments/open_range_v3/run.py), plus the archived records, establishes:

- Full diagnostics remain in controller archives, but the retrieved projection exposes only ID/domain/task/status, narrative lesson/hypothesis and aggregate validation counts. It omits the decisive counterexamples, executable correction and attempt trajectory. Archived evidence is not equivalent to information presented during reuse.
- Failed records are labeled failed/incomplete, not formally certified. Nevertheless, their unsupported narrative is supplied when no successful same-domain record exists. Selection prefers complete local validation, then recency; it does not measure informativeness.
- Earliest-best selection can retain the original failed explanation even when later prose acknowledges a contradiction. In the original run, unchanged code meant there was no verified correction to retain in any case.
- The original explicit-mapping task passed while its accompanying hypothesis described an incorrect mapping. Program correctness cannot confer truth on the explanation by association.
- A record citation is a declaration, not evidence of application or helpful transfer. The original experiment found no beneficial reuse.

[proposed_evidence_record.md](feedback_revision_20261014/proposed_evidence_record.md) specifies a minimal future record: original hypothesis; permitted contradictory input/expected/actual observation and oracle provenance; nullable revised hypothesis; before/after source hashes; independently measured executable status; separately unverified explanatory status; applicability/unknowns/counterexamples; immutable version links and uncertainty. Hidden answers remain controller-only unless a future protocol explicitly changes their lifecycle. Current task requirements retain authority over historical suggestions.

No retention schema, VSL, RiverBrain, FAISS, production memory, self-model or retrieval policy was changed. Improving storage cannot substitute for producing an actual correct revision; that remains the immediate historical-task bottleneck.

**8. Cost, containment and resource accounting**

| Phase | Model requests | Candidate launches | Controller seconds | Prompt / completion tokens |
|---|---:|---:|---:|---:|
| Main A/B/C + confirmation | 18 | 37 | 729.94 | 12,351 / 3,586 |
| Presentation follow-up | 6 | 21 | 61.83 | 4,591 / 740 |
| Total | **24** | **58** | **791.77 (13.20 min)** | **16,942 / 4,326** |

Launches reconcile to 28 qualification controls, three original-program baselines, 24 submitted programs, and three successful fresh-process replays. Every charged launch has durable begin/launch evidence. Four intentional timeout controls behaved as expected; no experimental task candidate timed out or failed to execute. All proposals parsed. All 24 service responses completed with `stop`, not `length`. Total recorded request latency was 743.81 seconds. Controlled evaluator calls account for 41.94 seconds excluding the four filesystem-control durations and surrounding overhead; controller elapsed time includes all execution overhead.

On the primary task, four A requests took 77.53 seconds and 231 output tokens; B took 116.84 seconds/741 tokens; C took 143.15 seconds/777 tokens. These are observed bills, not clean speed comparisons: live Echo shared the service, and residency/cache/load were uncontrolled. C did not establish an advantage over B warranting its extra output. There was no paid inference, installation or hardware expenditure.

Each request/launch is charged before operation, with cumulative caps across both freezes. Request timeout is bounded by remaining execution time; child timeout is 10 seconds. One experimental model call runs at a time. Memory monitoring samples free+inactive+speculative pages and stops after repeated estimates below 512 MiB. Lowest observed estimates were about 1.83 GiB in the main run and 4.94 GiB in the supplement; these are neither process peak measurements nor enforced allocation limits. No monitored distress stop occurred.

Both rooms in both phases passed legitimate own-root reads, production Skill A/historical Skill B/opposite-root/hidden-canary/historical-answer denial, production and surrogate write-open denial, scratch-symlink escape denial and relative-path controls. Multi-file correctness, wrong value, bool/int distinction, exception, input mutation and timeout controls passed. Expected values stayed in the trusted parent. The durable observer recorded results before cleanup. The controller guard denied its explicit production write probe; no unexpected guard denial occurred.

Limits remain: the controller hook protects trusted code, rather than being an OS sandbox for arbitrary controller code; candidate containment is OS-enforced. The batch observation wrapper shares a process with the candidate and is not proof against all malicious observation tampering. We measured returned values/types, exceptions and input mutation, not arbitrary global effects, identity or general Python correctness. These limits were inherited and not weakened during the diagnostic.

**9. Closing integrity and reproducibility**

Both runs exited normally. Main closing verification found all 971 pinned files unchanged; supplemental closing verification found all 1,233 pins unchanged, including the completed main evidence. These counts overlap and must not be added. The closed Open Range delivery manifest and its 626 entries remain intact. Frozen protocols, production skill records, evaluators and source authorities were not rewritten.

Echo PID 6316 (started October 8, 14:41:11), Ollama PID 1991 (September 19, 10:57:03), Studio 6048, parent shell 5713 and resource tracker 6318 retained their observed identities/start times. The shell is not independently established to be a watchdog. See [opening_processes.txt](feedback_revision_20261014/opening_processes.txt) and [closing_processes.txt](feedback_revision_20261014/closing_processes.txt). No service was signaled or restarted. A restricted tool invocation could not read `ps`; the authorized host read succeeded without altering services.

Live mutable FAISS, metadata, RiverBrain, self-model, self-edit convergence and temporary self-edit state changed between snapshots. They were excluded from experimental input, denied to candidate writes, and not written by this research controller. Snapshot differences alone do not identify their writer. This report asserts no experimental production mutation; it does **not** assert global byte stability while Echo runs.

The only mission additions are `app/experiments/feedback_revision/`, `audits/feedback_revision_20261014/`, this report and its checksum. [closing_repository.json](feedback_revision_20261014/closing_repository.json) and [delivery_manifest.json](feedback_revision_20261014/delivery_manifest.json) enumerate exact files, hashes, current git state and pin checks. All fourteen pre-existing tracked-modification paths remain; staged changes remain empty and HEAD remains unchanged. Unpinned pre-existing mutable content is not claimed byte-identical merely from git status. Nothing was staged, committed, pushed, reset or cleaned.

The frozen [requests](feedback_revision_20261014/requests/), [supplemental requests](feedback_revision_20261014/presentation/requests/), tasks, seeds and model hashes permit independent reconstruction. Each `*_response.json` contains full service bytes/counters; `*_proposal.json` preserves parsed files; `*_score.json` contains expected-versus-observed classification; per-room observer files contain argv/stdin/environment/stdout/stderr/exit/comparison events. Hash-chained journals verify both sequences. No expected values were fed back after hidden scoring.

Read-only reconstruction and fresh-run commands are in [REPRODUCE.md](feedback_revision_20261014/REPRODUCE.md). Fresh experimental reproduction must use a new output path, retain the same cumulative limits and run through the qualified host sandbox arrangement. Repeated model calls may vary despite fixed seeds; reproducing the archived scoring is distinct from guaranteeing byte-identical sampling. Existing namespaces must not be rerun or overwritten.

**10. Smallest justified next action**

Stop this mission; do not retry with more tokens or a bigger model. The next narrowly useful diagnostic is **evidence extraction versus executable integration**: under a new freeze, ask the same model to derive the local code-to-category facts and output-key obligation from diagnostic observations without requesting code, commit that model-generated intermediate record, then test whether it can revise the program using its own committed facts. Compare against a matched direct-correction control with equal total request/token budget and no hidden feedback. Do not supply the mapping or replacement program yourself. This would separate incorrect fact extraction from failure to incorporate correctly extracted facts; it should precede a retention redesign or another developmental campaign.

This recommendation is not executed here. The current result demonstrates bounded correction capability and identifies where the original correction pipeline stopped. It does not demonstrate acquired retained competence, successful convention transfer, or that experience makes future Echo better overall.
