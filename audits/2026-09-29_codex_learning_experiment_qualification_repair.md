# Qualification failure autopsy: oracle misses, evaluator validity, and ledger repair

Date: 2026-09-29, America/Los_Angeles (PDT, UTC−07:00). Investigator: Codex.

## 1. Executive Verdict

**QUALIFICATION STILL FAILS**

The original failure was real. All three equality-conditioned model outputs implemented **AND**, not equality. They failed exactly when both relevant features were zero: 16 of 64 inputs per policy. An independent truth-table reconstruction agrees with every saved evaluator decision. There is no demonstrated evaluator bug to repair.

The alleged oracle was **a privileged natural-language instruction given to the same model**, not an executable oracle. Its information was sufficient, but the model did not reliably translate it into the required policy. This is an oracle-control failure expressed as a generated-policy representation error. It is not evidence that Echo failed to learn: no autonomous learning treatment ran.

The separate ledger defect was demonstrated and repaired additively. The old writer overwrote an artifact hash with an event hash under the same dictionary key. This was a field-name/preimage defect, **not a cryptographic SHA-256 collision**. The original files and ledger remain untouched. The new writer passes focused identity and tamper checks.

One prospectively frozen qualification repeat retained the original prompts, model, seeds, evaluator, and ≥90% per-policy gate. All nine original-set policies were byte-identical to their earlier outputs. The repeat again yielded **50% baseline, 87.5% privileged-control mean, and three policies at 75%**. The repaired ledger cannot fix this semantic failure.

The separately frozen new-world check stopped on a 180-second Ollama response timeout. Of 18 scheduled qualification calls, 12 were initiated, 11 returned, one timed out, and six were not attempted. The timeout is **infrastructure failure, not task incorrectness**. There was no retry, timeout adjustment, prompt tuning, or continuation into acquisition. New-world qualification is incomplete.

**Integrity qualification:** this mission did not stage, commit, push, or control production processes. Concurrent work advanced HEAD by four commits and added unrelated research files. All 41 historical files fingerprinted at entry and all eight source files frozen for this qualification still match their hashes. Repository-wide claims such as “HEAD unchanged” or “nobody ran a learner elsewhere” would be false or unverified; the scope statements below concern this mission.

## 2. Previous Qualification Failure

The [previous report](2026-09-29_codex_interrupted_learning_experiment_resume.md) was read in full before investigation. Its SHA-256 remains `707dc2a9542bdea7f86232be67d3fd0c9db439b18ef745454e6cae012eb4e37c`. It specified no alternative continuation-report path.

Primary evidence is preserved in [the original qualification directory](../memory/experiments/counterfactual_acquisition/20260929_resume_v1/). The [original artifact manifest](../memory/experiments/counterfactual_acquisition/20260929_resume_v1/qualification_artifact_manifest.json) contains 38 entries; all verified before repair. The new entry inventory additionally covers the manifest itself and the previous report and sidecar: 41 preserved files in total.

The relevant unchanged source is [design.py](../app/experiments/counterfactual_acquisition/design.py), [policy.py](../app/experiments/counterfactual_acquisition/policy.py), [worker.py](../app/experiments/counterfactual_acquisition/worker.py), [controller.py](../app/experiments/counterfactual_acquisition/controller.py), and [checks.py](../app/experiments/counterfactual_acquisition/checks.py). These five historical source files were not edited.

**Exact apparatus:** six binary features, zero-based indices 0–5, all 64 binary vectors. Each development world selects two features. Side 0 and side 1 have complementary rules. Three development seeds were `910421`, `910422`, and `910423`, selecting `(2,4)`, `(2,3)`, and `(3,5)`, respectively, all with orientation 0. Therefore side 0 requires inequality/XOR and side 1 requires equality/XNOR.

Each world produced one blind policy and two privileged-instruction policies. All prompts contained the same 16 input/action records within that world, with feedback **WITHHELD**. Privileged prompts additionally stated the actual relation and feature indices. No PASS/FAIL experience was supplied to the model.

| Setting | Recorded value |
|---|---|
| Model requested and returned | `qwen2.5-coder:7b` |
| Registry digest | `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364` |
| Model details | 7.6B, Q4_K_M |
| Ollama version | 0.34.2 |
| Temperature / top_p | 0 / 1.0 |
| Output / context budget | 768 / 4096 |
| Sampling seeds | 813000, 813001, 813002, shared across the three conditions within each world |
| API mode | `/api/chat`, JSON format, non-streaming, exact system/user messages |
| Original completion | All nine `done_reason=stop`; no empty or length-terminated generation |
| Original tokens | Blind: 635 prompt / 44 output; privileged: 661 / 22 |

The requested model was not `echo:latest`. Qualification concerned the explicitly selected local model through isolated experiment scaffolding, not live Echo routing or its production memory.

The common instruction specified the closed Boolean expression language. The privileged sentence was exactly:

> External oracle information (qualification only): the target is true exactly when feature i and feature j are equal [or different]; otherwise false.

Here `i`, `j`, and the bracketed alternative denote the actual substituted values. Every exact prompt is retained in `calls/*.request.json`; every exact response is in `calls/*.response.json`. [Autopsy reconstruction](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/autopsy_reconstruction.json) embeds the nine exact requests, raw policies, histories, settings, and hashes for review.

Original run timing: approximately 13:55:31–13:55:53 UTC (06:55 PDT). There were nine generation calls and nine fresh consumption processes. Nine policies ×64 inputs =576 executed Boolean predictions. Scoring each blind policy against both complementary targets produces **768 correctness comparisons**, not 768 independent model observations.

| Original call | Intended relation | Returned policy | Correct / denominator |
|---|---|---|---:|
| dev_0_blind | Unknown | B below | 32/64 side 0; 32/64 side 1 |
| dev_0_oracle_0 | x2 different from x4 | XOR(x2,x4) | 64/64 |
| dev_0_oracle_1 | x2 equal to x4 | AND(x2,x4) | 48/64 |
| dev_1_blind | Unknown | B | 20/64 side 0; 44/64 side 1 |
| dev_1_oracle_0 | x2 different from x3 | XOR(x2,x3) | 64/64 |
| dev_1_oracle_1 | x2 equal to x3 | AND(x2,x3) | 48/64 |
| dev_2_blind | Unknown | B | 32/64 side 0; 32/64 side 1 |
| dev_2_oracle_0 | x3 different from x5 | XOR(x3,x5) | 64/64 |
| dev_2_oracle_1 | x3 equal to x5 | AND(x3,x5) | 48/64 |

All three blind outputs were byte-identical:

```json
{"policy":["or",["and",["not",["feature",0]],["feature",1]],["and",["feature",2],["feature",3]]]}
```

Whitespace in the original response is preserved in the raw artifacts; this display is compacted for readability.

## 3. Exact Failed Cases

The complete requested case table is [original_development_case_table.csv](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/original_development_case_table.csv): **384 rows**, one per world/side/vector, with `Case`, `Input`, `Baseline`, `Oracle`, `Expected`, `Score`, `Baseline_score`, `Reason`, relevant features, relation, and whether the vector appeared in the prompt. `Score` is privileged-policy correctness; baseline correctness has its own column. All 768 original comparisons are represented without duplicating the joined inputs.

The table below specifies every oracle failure compactly. Input strings are six bits ordered x0…x5. Every listed row has oracle output `false`, independent expected output `true`, and oracle score 0. Baseline outputs vary and are recorded individually in the CSV.

| Failed policy | All 16 failing vectors |
|---|---|
| dev_0_oracle_1, features (2,4) | 000000, 000001, 000100, 000101, 010000, 010001, 010100, 010101, 100000, 100001, 100100, 100101, 110000, 110001, 110100, 110101 |
| dev_1_oracle_1, features (2,3) | 000000, 000001, 000010, 000011, 010000, 010001, 010010, 010011, 100000, 100001, 100010, 100011, 110000, 110001, 110010, 110011 |
| dev_2_oracle_1, features (3,5) | 000000, 000010, 001000, 001010, 010000, 010010, 011000, 011010, 100000, 100010, 101000, 101010, 110000, 110010, 111000, 111010 |

The exact same vectors are not responsible in every world. Pairwise failure-set intersections are 8, 4, and 8 vectors; the three-way intersection is 4. The common cause is the **both-zero equality subcase**, not a shared case ID or a special fixed input.

## 4. Independent Ground Truth

Ground truth was first reconstructed without importing the tested `expected()`, `predict()`, or `grade()` functions. A separate four-row truth table supplied equality and its complement. The raw saved expressions were also independently interpreted and compared with every saved successor output.

| Relevant feature values | Equality target | Inequality target | Returned AND | Equality score |
|---|---:|---:|---:|---:|
| 0,0 | true | false | false | Incorrect |
| 0,1 | false | true | false | Correct |
| 1,0 | false | true | false | Correct |
| 1,1 | true | false | true | Correct |

The other four features can take 16 combinations. Thus the 0,0 error necessarily yields 16 failures and 48 successes. Equality has no reasonable interpretation here under which zero equals zero is false: binary features and indices are explicitly specified. No hidden convention or out-of-domain case is needed to establish this result.

Every original successor output matches independent execution of its saved policy. Every recomputed score matches the saved score. Every original request digest, state digest, raw-response-to-state mapping, and successor state digest agrees. No correct generated equality policy was wrongly rejected.

## 5. Oracle Validity

The actual transformation was supplied **in language**, not as an already correct executable policy. The model still had to translate it into the permitted representation. That step was fallible. Supplying complete information did not guarantee correct use of the information.

The original condition is a legitimate **known-rule headroom test**, but calling it an infallible oracle overstates what it provides. Its failure can invalidate qualification without invalidating the Boolean task or scorer.

For each of the 48 misses, the causal trace is the same, with the relevant feature indices substituted:

| Boundary | Intended value | Actual evidence | Assessment |
|---|---|---|---|
| Task generator | Equality for orientation 0, side 1 | Independent truth table agrees with generated targets | Correct |
| Task representation | Six binary values, zero-based indices | Exact request grammar says 0–5 | Correct; no indexing shift |
| Privileged information | True iff xi equals xj | Saved sentence explicitly says `equal` | Complete correct information |
| Prompt assembly | Add that sentence to the blind request | Removing exactly that sentence restores the blind prompt | No substitution/serialization loss |
| Model invocation | Request correct policy from specified model | Correct model label/digest check and settings; completed response | Translation remains the model's responsibility |
| Returned policy | Equality, representable as NOT(XOR) or equivalent | AND(xi,xj) | **First observable semantic divergence** |
| Parser | Preserve a valid expression | AND is valid; no repair or extraction | Faithful |
| Persistence / consumption | Store and execute that exact expression | Hashes and all saved outputs agree | Faithful |
| Scoring | Compare output with actual equality target | Both-zero cases marked wrong | Correct |

**Classification:** ORACLE FAILURE and POLICY REPRESENTATION FAILURE, located in the model-generated instruction-to-policy translation. EVALUATOR FAILURE, TASK AMBIGUITY, and scoring-related EXPERIMENTAL PLUMBING FAILURE are not supported for these misses. MODEL VARIANCE was initially unresolved; the exact repeat reproduced every original policy, supporting a systematic failure under these prompts/settings. Two runs do not establish behavior under all seeds, prompts, backend loads, or model configurations.

It would be possible to hand the consumer a correct NOT(XOR) policy. That validates the interpreter, not this model's known-rule performance. Substituting it for the failed model control would bypass the original gate. Likewise, teaching the model the observed missing subcase, adding an equality primitive, selecting only inequality worlds, or changing the common learner prompt would be an additional intervention, not a demonstrated scorer repair. None was done.

## 6. Evaluator Validity

`policy.py` accepts only a bounded Boolean AST; it does not execute model-supplied Python. Operations are constants, feature lookup, NOT, AND, OR, and XOR. Invalid JSON, duplicate keys, extra fields, invalid indices/arity, oversized or excessively nested expressions are rejected. Scoring requires a nonempty Boolean expected corpus and exactly matching output cardinality. Integers, nulls, and status objects cannot count as correct Boolean results.

The consumer receives a state path/hash and input vectors. It receives no expected array, generator metadata, or scoring function. The trusted controller retains expected values. A policy cannot read its filename, filesystem, process frames, or evaluator state through the AST language. This is a closed-data interpreter, not a claim about arbitrary hostile Python sandbox security.

New diagnostic tests cover **all 15 feature pairs**, both relations, and all 64 inputs using an independent truth table: correct policies score 100%; opposite policies score 0%; AND near misses score 75% against equality, failing exactly the both-zero inputs. These diagnostics supplement, rather than replace, the model gate.

No evaluator implementation change was justified or made. Qualification does not generalize this finite Boolean evaluator to AP-0, F2, arbitrary code, or open-ended task correctness.

## 7. 50% vs 87.5% Development Result

Original baseline: **192/384** correctness comparisons across three blind policies, each scored against two complementary worlds. Privileged controls: **336/384**, from three 64/64 inequality policies and three 48/64 equality policies. Difference: **144 additional correct comparisons, or 37.5 percentage points** on this finite corpus.

There is mechanistically meaningful control separation in the recorded outputs. All six privileged policies used the instructed feature pair; all inequality instructions produced exact XOR, while equality instructions produced the same specific AND error. Mere response length does not explain that detailed correspondence by itself. However, this was not a randomized content-versus-length experiment: the extra sentence added 26 prompt tokens and both explicit information and an “oracle” framing cue. There was no matched neutral-sentence control. Therefore the difference is a **qualification observation**, not isolated evidence of learning, memory benefit, or a unique psychological mechanism.

An important denominator limitation: **pooled blind accuracy is forced to 50% whenever a valid Boolean policy is scored against both complementary worlds**. Each prediction is right in exactly one world. This is not an estimate of chance with 384 independent Bernoulli trials. The ≤55% pooled gate catches some implementation problems but provides little discrimination among valid blind policies; per-world scores still matter. Here they ranged from 31.25% to 68.75%. The original criterion was retained rather than silently strengthened or weakened.

For a fixed policy evaluated on the entire finite domain, its reported accuracy is exact; a binomial confidence interval over those 64 rows would imply an unsupported sampling model. Generalizing to model generations or worlds has only three world configurations and six privileged generations, paired within worlds, with repeated prompts and no independently sampled acquisition histories. No valid population confidence interval or p-value for general oracle reliability follows from treating 384 rows as independent. The complete original repeat adds evidence of repeatability under the same requests, not six new independent task families.

## 8. Three 75% Policy Failures

The three failures share all load-bearing characteristics:

- Same task subtype: equality, not inequality.
- Same incorrect operation: AND, with the correct feature indices.
- Same omitted truth-table row: both relevant inputs zero.
- Same valid parser path, 22 output tokens, and normal stop completion.
- Same failure after byte-identical request replication.

They do not share precisely the same full input vectors. Their misses occurred both on vectors shown in WITHHELD prompt records and on other vectors:

| Equality policy | Correct on 16 prompt-shown inputs | Correct on 48 other inputs |
|---|---:|---:|
| Features (2,4) | 12/16 | 36/48 |
| Features (2,3) | 11/16 | 37/48 |
| Features (3,5) | 13/16 | 35/48 |

All inequality policies scored 16/16 and 48/48, respectively. The 75% result is not a failure confined to novelty, prompt membership, a particular serialized vector, or one parser branch. It follows from the returned operation's semantics.

## 9. Synthetic / Real Discrepancy

The original 35 synthetic checks were reconstructed from source and their saved results, then rerun unchanged. All passed originally and again in this mission:

| # | Original check | Original / fresh |
|---:|---|---|
| 1 | Extra verdict field | PASS / PASS |
| 2 | Duplicate key | PASS / PASS |
| 3 | Nonfinite | PASS / PASS |
| 4 | Numeric Boolean | PASS / PASS |
| 5 | Filesystem operation | PASS / PASS |
| 6 | Runtime introspection | PASS / PASS |
| 7 | Unknown operation | PASS / PASS |
| 8 | Multiple JSON documents | PASS / PASS |
| 9 | Trailing success marker | PASS / PASS |
| 10 | Negative index | PASS / PASS |
| 11 | Boolean feature index | PASS / PASS |
| 12 | Out of range | PASS / PASS |
| 13 | Bad arity | PASS / PASS |
| 14 | Oversized | PASS / PASS |
| 15 | Depth bound | PASS / PASS |
| 16 | Node bound | PASS / PASS |
| 17 | Empty expected | PASS / PASS |
| 18 | Empty result | PASS / PASS |
| 19 | Short result | PASS / PASS |
| 20 | Extra result | PASS / PASS |
| 21 | Integer cannot spoof Boolean | PASS / PASS |
| 22 | Status object cannot spoof result | PASS / PASS |
| 23 | Null is wrong | PASS / PASS |
| 24 | Independent reference exhaustively agrees | PASS / PASS |
| 25 | Only feedback differs in counterfactual experience | PASS / PASS |
| 26 | Blind receives same inputs/actions | PASS / PASS |
| 27 | Request has no routing/history/tools | PASS / PASS |
| 28 | Model prompts lack world identifiers | PASS / PASS |
| 29 | Train/eval disjoint and nonempty | PASS / PASS |
| 30 | Opposite worlds are exactly complementary | PASS / PASS |
| 31 | Constant controls fail half the cases | PASS / PASS |
| 32 | Contextual fixed policy averages one-half across worlds | PASS / PASS |
| 33 | Exact-input memorizer has no held-out benefit | PASS / PASS |
| 34 | Fresh successor loads exact state | PASS / PASS |
| 35 | Changed state refuses consumption | PASS / PASS |

The missing discrimination dimension was **model translation of a correct natural-language rule into a semantically correct policy**. The synthetic suite directly supplied correct expressions; it never asked the LLM to produce them. It did exercise real subprocess consumption, disk recovery, parsing, and exhaustive interpreter semantics. It did not exercise a production sandbox, because no arbitrary generated code is executed in this design.

The second uncovered dimension was ledger round-trip provenance: the suite did not construct and independently verify a STATE_FROZEN event. A green parser/interpreter suite could not establish either model headroom or correct ledger serialization. The live qualification correctly caught the former; forensic rehashing caught the latter.

The disjointness check tests the prospective split construction. The development qualification intentionally evaluated all 64 vectors, including the 16 input vectors already present in WITHHELD records. That is not a completed hidden-transfer experiment. It must not be reported as one.

## 10. Ledger Hash Collision

The defect is at historical `controller.py` lines 31–42 and 94–98:

```python
row = {"utc_ns": ..., "kind": kind, "previous": previous, **data}
row["hash"] = digest(row)
```

For STATE_FROZEN, `data["hash"]` already contains the state digest. Python evaluates `digest(row)` while that artifact hash is in the preimage, then overwrites the field with the event digest. The stored event therefore lacks one field needed to reproduce its own hash.

All 21 original ledger events have correct predecessor links. Ordinary “remove hash and rehash” verification fails exactly at lines **3,5,7,9,11,13,15,17,19**: the nine STATE_FROZEN events. Inserting the correct state hash, recovered from the separately preserved state file, reconstructs each original preimage and matches all nine stored event hashes.

A minimal in-memory demonstration is recorded in [autopsy_reconstruction.json](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/autopsy_reconstruction.json). For example, state `{"raw_policy":"{\"policy\":true}"}` has digest `180b8af8d50f1735884455bca4b7924033cd5a390ba650d456b1b91a1e9922fd`; the serialized fixed-timestamp demonstration instead stores event hash `500767c9e075066e38f0ae6cf1adc3c2b86a12100b823c301c04d9356e122365` under `hash`. The ordinary rehash fails. A different false-policy state yields a different artifact hash and a different event hash; **two distinct objects did not collide cryptographically**.

The new regression also invokes the actual unchanged historical writer against harmless temporary states, reproducing the defect. No historical ledger was edited during reproduction.

## 11. Collision Impact

| Question | Finding |
|---|---|
| Identical field name / overwritten key? | Yes: artifact hash and event hash use `hash`; the artifact identifier is overwritten. |
| Hash truncation or SHA collision? | No evidence of either. |
| Distinct states indistinguishable? | Not in the preserved state files or result records. Their hashes differ. The ledger no longer explicitly identifies the state by its intended hash field. |
| Misattribution possible? | Yes: a future reader could interpret the event digest as the state digest, or reject a valid artifact against the wrong hash. |
| Can validation compare the wrong object? | Yes for consumers treating the flattened ledger field as the artifact hash. Ordinary event verification already fails. |
| Did original scoring use that wrong field? | No. `acquire()` returned the original record; `**record` created a separate dictionary. `consume()` used the original correct state hash, confirmed in all saved successor records. |
| Historical evidence contaminated beyond recovery? | No. Requests, responses, retained files, result records, and reconstructed preimages agree. The original ledger is defective but interpretable with external evidence. |
| Future acquisition risk? | Yes if v1 writer is reused or a consumer trusts ambiguous ledger fields. Historical `controller.py` remains defective by design, preserved as evidence. |

A valid hash chain is not a signature, proof of authorship, or protection against rewriting an entire chain and its untrusted root. A terminal prefix deletion also needs an independently retained tail/manifest to detect. The repair does not claim those stronger properties.

## 12. Contamination Analysis

**Source-supported exclusions:** the call path uses the direct local Ollama API with exactly one system and one user message. It imports experiment-local modules and the standard library, not RiverBrain, VSL, FAISS, production memory, self-edit, council routing, or an attempt-ledger prompt reader. The worker has no code path that consults earlier experiment states. Each call and consumer runs in a fresh Python subprocess with restricted environment, a temporary working directory, closed inherited descriptors, and `-I -B`.

Model-facing JSON has no world ID, side label, state filename, evaluator outputs, tools, retrieval results, or previous chat history. The privileged sentence intentionally discloses the actual relation only in the qualification control. No evaluated acquisition feedback is delivered to the model. Expected values remain controller-side; a closed policy expression cannot access them.

All original raw requests match reconstruction. Within a world, removing the added privileged sentence makes its request prompt identical to the blind prompt. The three policies share sampling settings and budgets. The original-repeat request files are **byte-identical** to the nine original request files.

**Duplication:** all development worlds reuse the 64-vector domain, and all three original blind output strings match. Neither fact supplies an experience-dependent mechanism. The benchmark's finite-domain repetition is explicit, and no transfer claim is made. The new-world check changes the latent feature pair and prompt records, not the six-bit input universe.

**Unknowns:** the shared Ollama backend was not reset. Backend caching, scheduling, and numerical nondeterminism were not independently instrumented. There is no response-cache mechanism in this client; responses have separate timestamps and token counts, but that does not prove absence of all backend caching. Identical outputs alone are not evidence of cross-call learning or cache contamination.

Other work later added learner scripts in this namespace. File birth times are after this qualification stopped; none is imported by the frozen apparatus, and all frozen source hashes still match. Their contents and outcomes were not read or used to select this report's conclusion. See [concurrent-work boundary](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/concurrent_work_boundary.json). These checks bound contamination of this run; they do not audit all concurrent research.

## 13. Root Cause(s)

1. **Model-generated policy representation failure:** equality instructions became conjunction. This causally explains every original oracle miss, with no reliance on the tested evaluator's own correctness assertion.
2. **Control-description overstatement:** “oracle” meant privileged information plus a fallible model translation step. The task information was sufficient; the produced policy was not correct. The known-rule gate failed honestly.
3. **Ledger bookkeeping defect:** an overwritten hash field destroyed explicit artifact identity within nine event rows and ordinary event rehashability. It did not cause the 75% policies or their scores.
4. **Fresh-check infrastructure failure:** a new-world request timed out before a response was received. The preceding request reported 169.879 seconds total, including 155.463 seconds load duration; this supports a service-latency concern. It does not identify whether loading, scheduling, shared resource pressure, or another backend condition caused the next timeout. No wrong answer is inferred from silence.
5. **Partial-result durability limitation exposed by that stop:** requests, returned policies, and state records were saved per call, but successor outputs were accumulated in memory until the batch result was written. The first two new-world successor result objects are therefore not durably available after the later timeout. Their policy behavior can be independently reconstructed, but reconstructed values must not be relabeled as saved execution observations. This limitation was documented without a post-freeze repair.

The final two findings do not alter the completed original-set repeat. Its full result and successor outputs were durably written before the new-world timeout.

## 14. Repair Eligibility

| Proposed change | Classification | Reason / disposition |
|---|---|---|
| Separate artifact and event hash fields; envelope/payload namespacing; verifier | **ELIGIBLE** | Demonstrated provenance defect, unrelated to task answers; original scientific claim and gate unchanged. Implemented additively. |
| Rename the interpretation in documentation to privileged-instruction control | **ELIGIBLE** | Corrects an overstatement without changing prompts or semantics. Used in this report and new result labels. |
| Add all-pairs independent gold/negative/near-miss evaluator diagnostics | **ELIGIBLE** | Tests measurement discrimination without modifying model inputs, learner, or target. Does not replace the original gate. |
| Change evaluator to accept AND on 0,0 equality cases | **NOT ELIGIBLE** | Would mis-score incorrect behavior and redefine success. |
| Replace model output with a hand-written correct policy for headroom qualification | **NOT ELIGIBLE** | Bypasses the failed model-application requirement. Valid only as a separately labeled interpreter diagnostic. |
| Coach the missing equality subcase, add a special primitive, select only inequality, alter model/prompt/seed to seek passing responses | **NOT ELIGIBLE as repair of demonstrated instrumentation defects here** | No source defect makes the original rule ambiguous or interpreter incorrect. Such changes require a separately reviewed design, not a claim that the existing gate passed. |
| Lower ≥90%, use only the pooled mean, or omit failed policies | **NOT ELIGIBLE** | Explicitly prohibited and scientifically changes the gate. |
| Change timeout or retry the interrupted new-world call after seeing failure | **NOT ELIGIBLE under this frozen repair plan** | Plan required stopping on infrastructure failure. No rerun was made. |
| Persist every successor result immediately | **UNCERTAIN for a future repair authorization; no change here** | New interruption exposed a concrete evidence-durability issue, but it was outside the frozen repair and was not fixed mid-run. |

## 15. Frozen Repair Plan

The [repair plan](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/repair_plan_frozen.json) was created at **15:26:17 UTC**, before the three new source files were implemented. SHA-256:

`3b0974d7408134a5fd3bb150441c8cac0be85bc951067c6867ad3496bdccc98e`

It specified the demonstrated ledger defect, separate event/state identities, regression requirements, preservation of all five old source files, unchanged prompts/model/evaluator/thresholds, one complete original repeat, three new development worlds, exact seeds/order, no semantic repairs, and stop-on-infrastructure-failure/no-retry rules. Running both sets after a **semantic** failure was prospectively allowed for diagnosis; infrastructure failure required immediate stop.

After offline tests passed, all eight source files and all 18 exact requests were frozen in [qualification_inputs_frozen.json](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/qualification_inputs_frozen.json) at **15:29:11 UTC**. SHA-256:

`b22ee0c543178737bdcbd46c626e5fc495f5d35c37adfe2b60decd77c4a86d92`

The source and request fingerprints were verified before execution and checked after it. No implementation or prompt change was made after this freeze. **This is a repair/qualification plan, not the main autonomous-acquisition protocol.** The main protocol remains unfrozen by this mission.

## 16. Repairs Performed

Exactly three new source files were added to the isolated experimental namespace:

| File | Purpose |
|---|---|
| [ledger_v2.py](../app/experiments/counterfactual_acquisition/ledger_v2.py) | Separate `event_hash`, `previous_event_hash`, sequence, timestamp, kind, and nested payload; explicit `state_hash` for STATE_FROZEN; verify existing chain before append; reject legacy/corrupt rows. |
| [repair_checks.py](../app/experiments/counterfactual_acquisition/repair_checks.py) | Reproduce old defect against temporary files, verify new provenance discrimination and tamper rejection, add independent evaluator diagnostics. |
| [qualification_repair.py](../app/experiments/counterfactual_acquisition/qualification_repair.py) | Freeze qualification inputs, run unchanged original call/consumption functions with only their event writer replaced locally, preserve new evidence separately, enforce unchanged gate and stopping rules. |

The original five source files were deliberately preserved. No repair was applied to the evaluator, parser, worker, model settings, common instruction, oracle sentence, task generator, production code, or learner. The new writer is used **only by the new qualification entry point**; invoking the old controller directly would still use its old defective writer. This is not a claim that every future call path has been migrated.

New evidence lives only under [20260929_qualification_autopsy_v1](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/), separate from the failed historical qualification. Temporary regression directories and subprocess working directories were created with `TemporaryDirectory` and cleaned by their owning contexts; no unrelated temporary artifacts were removed.

## 17. Regression Tests

[repair_regression_results.json](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/repair_regression_results.json) records **35/35 unchanged checks plus 18/18 added checks**. These are not 53 independent scientific experiments.

The first two new checks require the old implementation to exhibit the failure, rather than pretending it passes the repaired contract. The succeeding checks assert the corrected contract:

| # | Added check | Result |
|---:|---|---|
| 1 | Old writer overwrites artifact identity | Reproduced |
| 2 | Old serialized event cannot ordinarily rehash | Reproduced |
| 3 | Legacy rows rejected rather than silently migrated | PASS |
| 4 | New rows rehash from serialized data alone | PASS |
| 5 | State identity survives separately from event identity | PASS |
| 6 | Distinct state objects retain distinct identities | PASS |
| 7 | Repeated state has same artifact hash, distinct event hash | PASS |
| 8 | Payload field names cannot replace envelope fields | PASS |
| 9 | Tampered event hash rejected | PASS |
| 10 | Tampered predecessor hash rejected | PASS |
| 11 | Tampered sequence rejected | PASS |
| 12 | Tampered payload rejected | PASS |
| 13 | Interior row deletion rejected | PASS |
| 14 | Row duplication rejected | PASS |
| 15 | Append refuses corrupt chain without changing it | PASS |
| 16 | All-pairs gold policies agree with independent truth table | PASS |
| 17 | All-pairs opposite policies score zero | PASS |
| 18 | All-pairs AND near miss fails exactly both-zero equality | PASS |

The old code fails preservation/ordinary-rehash contracts; the new code satisfies them. Different true/false artifacts remain distinguishable. These tests address the mechanism, not just the three observed feature pairs. During actual qualification, an additional read-only verifier recomputed all **28 new ledger events**, including all 11 saved state identities, successfully.

## 18. Fresh Qualification

The new entry point was run once. All original-repeat inputs, seeds, and raw policy strings match their historical equivalents. All policies were valid JSON and stopped normally. No old responses were replayed as new evidence: distinct requests to the local service and their raw timestamped responses are preserved.

| Original-repeat policy | Baseline side scores or privileged score | Change from original |
|---|---:|---|
| dev_0_blind | 50%, 50% | None |
| dev_0_oracle_0 | 100% | None |
| dev_0_oracle_1 | **75%** | None |
| dev_1_blind | 31.25%, 68.75% | None |
| dev_1_oracle_0 | 100% | None |
| dev_1_oracle_1 | **75%** | None |
| dev_2_blind | 50%, 50% | None |
| dev_2_oracle_0 | 100% | None |
| dev_2_oracle_1 | **75%** | None |

The [completed original-repeat result](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/fresh_qualification/original_rerun/headroom_qualification.json) records `passed=false`, `baseline_mean=0.5`, `oracle_mean=0.875`, and `oracle_min=0.75`. Its 20-event ledger validates. Its complete successor outputs were preserved.

The model digest and Ollama version matched the frozen identity, and model identity was checked before each initiated call. The repeated equality failure therefore survived the provenance-only change. This is evidence against treating the original misses as ledger-induced scoring errors or an isolated first-run accident. It is not proof of universal determinism.

The whole invocation eventually exited **1 on infrastructure failure**, not the normal completed semantic-failure exit 2. No overall `qualification_result.json` was written because execution stopped during the new-world batch. The preserved completed original batch is still sufficient to reject qualification at the unchanged gate.

## 19. Anti-Overfitting Cases

Before implementation and before any new outcomes, the repair plan selected three new latent feature pairs absent from the original worlds. Selection used generator metadata only. At least one world reverses orientation to avoid equating “side 1” with equality in the new set.

| New-world seed | Pair | Orientation | Model seed | Completion |
|---:|---|---:|---:|---|
| 910425 | (1,5) | 0 | 814000 | Blind and inequality returned; equality request timed out |
| 910426 | (2,5) | 1 | 814001 | Not attempted after stop |
| 910429 | (1,2) | 0 | 814002 | Not attempted after stop |

These are new **task mappings and prompt histories**, not new binary input vectors: the original qualification already exhausted the six-bit domain. No task schema or scientific target was changed to create artificial novelty.

The completed blind response was `OR(AND(x0,x2),AND(x1,x3))`. The completed privileged inequality response was `XOR(x1,x5)`. Independent read-only reconstruction from these saved policies gives 50%/50% for the blind policy and 100% for the inequality policy. Because the batch crashed before saving its result object, these are labeled **reconstructed policy scores**, not a substitute for durably preserved original successor outputs.

The equality call `anti_overfitting/dev_0_oracle_1` began at **15:34:08.182814 UTC**. No response or state was saved for it. The root ledger recorded STOPPED at **15:37:08.255897 UTC**, with `TimeoutError: timed out` while waiting for HTTP response headers. The existing 180-second API timeout was not changed. Its score is **missing / infrastructure failure**, not 0%, 75%, or any inferred policy behavior.

Total for this mission's planned model calls: **18 planned; 12 initiated; 11 responses; 1 timeout; 6 unattempted**. No selective retries or exclusions were applied. [Fresh forensic reanalysis](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/fresh_readonly_reanalysis.json) identifies every scheduled call and its status. The [independent comparison table](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/fresh_qualification_independent_case_table.csv) distinguishes 768 comparisons against saved original-repeat successor outputs from 192 offline reconstructions for the two returned new-world policies.

**The new-world anti-overfitting check is incomplete, not passed.** The all-pairs offline diagnostics support the ledger/evaluator repair's generality, but cannot fill in the missing model qualification outcomes. No further repair or run was made after the prescribed stop.

## 20. Final Qualification Verdict

**QUALIFICATION STILL FAILS**

The completed repeated original set violates the unchanged ≥90% criterion in precisely the same three policies. The new-world set cannot supply a pass because it stopped incomplete. The ledger repair is qualified for its stated single-writer contract; the original headroom requirement is not.

This verdict is not EVALUATOR INVALID: scoring survived independent ground-truth and negative-control checks. It is not PROVENANCE INVALID: the historical defect is bounded and reconstructable, and the repaired ledger verifies. The natural-language control is not an infallible oracle, but the task is well-defined and its failed headroom test remains interpretable. This mission supplies no basis for saying that a changed oracle/task design has met the original requirement.

The apparatus is **not ready for this mission to freeze the main protocol**. No freeze or autonomous run follows this report.

## 21. What This Establishes

- The exact original 75% failures were incorrect model-generated policies, correctly measured.
- The equality relation was fully expressible in the supplied language, and its expected values were unambiguous.
- Privileged information improved observed finite-domain performance but did not reliably instantiate the correct policy at the required threshold.
- The 50% pooled blind score has an algebraic explanation and should not be mistaken for hundreds of independent baseline observations.
- The hash problem was a reproducible overwritten-field defect, not a SHA-256 collision; the original correctness evidence remains reconstructable.
- A bounded additive repair separates artifact identity from event identity and survives the specified regression and live-ledger checks.
- Exact repetition reproduced the original failure without prompt, model, evaluator, or threshold changes.
- A new-world service timeout revealed infrastructure and partial-result durability limits; neither was hidden or scored as model incompetence.

## 22. What This Does NOT Establish

**This mission does not test whether Echo can autonomously acquire competence.**

It does not establish inability to learn, persistent experience-caused improvement, reusable learned procedures, accumulated competence, or a positive/negative main acquisition result. No model received the true/shuffled acquisition treatment. The qualification functions are internally named `acquire`, and the fixed system prompt uses “learner,” but these calls contained only WITHHELD records plus optional externally supplied rules. Names do not turn them into autonomous experience extraction.

It does not establish that every equality prompt would fail, that all 7B models fail, or that a separately approved representation intervention could not work. It does not establish that backend caching or competing local workloads had no effect on latency. It does not establish anti-overfitting model qualification after a missing response. It does not convert offline reconstructed values into missing raw execution evidence.

Most importantly, it does not justify replacing the failed known-rule control with hand-authored executable answers and announcing that the original same-model gate passed.

## 23. Repository / Runtime Integrity

### Baseline and concurrent changes

First repository observation: **2026-09-29 08:18:23 PDT**. Detailed entry fingerprints were saved before any source repair in [entry_provenance.json](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/entry_provenance.json), including full expanded status, staged state, 1,211 tracked-file hashes, and the 41 relevant historical files.

| Item | Entry | Exit integrity check |
|---|---|---|
| HEAD | `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0` | `e5acbb09cece8d1791fa6d967fe57067137a8cff` |
| origin/main, local tracking reference | `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0` | Same |
| Ahead / behind | 0 / 0 | 4 / 0 |
| Staged changes | Empty | Empty |
| 41 historical relevant files | Fingerprinted | All unchanged |
| Eight frozen apparatus sources | Frozen before new calls | All unchanged |

No fetch was performed; `origin/main` above is the local remote-tracking ref, not a fresh remote query.

The 11 tracked dirty paths at entry were `CLAUDE.md`, `PENDING_DECISIONS.md`, `app/core/self_edit_convergence.json`, `app/core/self_edit_generated.py`, `app/core/temporal_environment.py`, `claude_relay/.last_seen_from_air.json`, `claude_relay/.last_seen_from_air_hub.json`, `claude_relay/from_m5.md`, `logs/janitor_report.json`, `sandbox/scripts/temp_self_edit.py`, and `staging/self_edit_candidate.py`. Existing untracked audits, relay/hub artifacts, scratch files, and the five experiment sources are fully enumerated in the entry record and were not treated as disposable scratch.

The four concurrent commits concern relay cursors, hub attribution, optional relay supervision, and consumer-name validation. Their recorded commit times are 08:40:10–08:50:56 PDT, after this qualification stopped at 08:37:08. They do not change the frozen call/evaluation source. Current tracked-file differences relative to entry include relay/hub source plus live `logs/janitor_report.json` and `sandbox/scripts/temp_self_edit.py`; this mission did not write them. Full exit status is in [exit_integrity.json](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/exit_integrity.json).

Concurrent additions include `phase2_requalify_different.py`, `phase4_learner_ab.py`, `phase5_revision_after_contradiction.py`, `phase6_grammar_reminder.py`, `phase7_crossed_repair_design.py`, and other investigators' reports. Their observed birth times begin at 16:22 UTC, after this run stopped. They were not read substantively, imported, executed, edited, or interpreted here. Their existence does not authorize this mission to resume acquisition or revise its frozen gate. It also prevents a global claim that all repository research remained stopped.

### Runtime

Live Echo stayed **PID 71538**, parent 56610, started **September 28 at 19:15:54 PDT**. Its observed uptime increased from about 13h08m before qualification to 16h40m34s at the final recorded process check. Its resource tracker stayed PID 71548. Ollama serve stayed **PID 1991**, started September 19 at 10:57:03 PDT. [Runtime observations](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/runtime_observations.txt) preserve the checks.

No restart, stop, signal, unload, production self-edit, memory mutation, or production routing call was issued by this mission. Local qualification did use the shared Ollama service and therefore consumed compute; it was not isolated from all resource contention. No attempt was made to cancel an individual server-side request after the client timeout; backend cancellation behavior was not independently observed.

### Exact scope of writes and remaining authorization

This mission created the three source files listed in §16, this report, and the additive autopsy/qualification evidence directory. The final **[mission artifact manifest](../memory/experiments/counterfactual_acquisition/20260929_qualification_autopsy_v1/mission_artifact_manifest.json)** enumerates and fingerprints every permanent file created by this mission, excluding only its own self-hash. It does not claim ownership of concurrent files. All original evidence and previous reports remain byte-for-byte unchanged.

Confirmed for this mission:

- Live Echo not restarted; production Echo, RiverBrain, canonical VSL, and production memory not modified.
- Autonomous learner not run; no main acquisition trial; main protocol not frozen.
- Original ≥90% per-policy qualification threshold unchanged.
- No semantic edits to model outputs; no discarded returned policies; no selective retries.
- No files staged; no commits or pushes issued by this investigator. **HEAD nevertheless changed concurrently**, as disclosed above.
- New source/report files remain untracked and unstaged; generated evidence is additive in the experiment artifact directory.

Return this diagnosis and ledger-only repair for review. The remaining blocker is failed same-model known-rule qualification, plus an incomplete new-world check and its recorded infrastructure/evidence-durability limitations. Do not infer authorization for a replacement oracle, prompt intervention, further qualification run, main protocol freeze, or acquisition trial from this report.
