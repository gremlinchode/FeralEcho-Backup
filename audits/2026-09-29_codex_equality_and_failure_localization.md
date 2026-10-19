# Equality → AND: independent backward forensic localization

2026-09-29 · Codex · America/Los_Angeles, PDT (UTC−07:00)

**Finding:** the first observable substitution is already present in the raw model-service response. The world, target sentence, request serialization, DSL capacity, parser, persistence, executor, and evaluator do not introduce it. A fresh original-request probe again returned AND.

**New evidence:** all three separate, no-DSL conceptual probes failed to predict equality, even with the relevant features supplied and direct target observations available. Two descriptions contradicted their own predictions. A correctly recognized equality intermediate was therefore **not demonstrated**. The frozen prerequisite for additional translation/context probes failed; those four calls were skipped, not improvised around.

**Disposition:** **E3 is observed in the new conceptual diagnostic.** For the original generations, the finer distinction between misunderstanding the supplied equality relation and incorrectly encoding a correctly understood relation remains **E8 / unresolved**. Calling the original failure a proven “knows equality but cannot express it” defect would exceed the evidence. The generation interface is localized; the internal cognitive step is not.

Nothing was repaired. The old qualification remains failed, the interrupted new-world check remains incomplete, and no autonomous learner or acquisition trial ran in this mission.

## 1. Ground truth and repository provenance

The starting [qualification-repair report](2026-09-29_codex_learning_experiment_qualification_repair.md) was inspected, then its claims were reconstructed from the original requests, raw responses, retained state files, result records, and unchanged source. Its prose was not used as the ground-truth oracle.

| Repository/runtime item | Observation |
|---|---|
| Branch | `vsl-implementation` |
| HEAD, entry and exit | `e5acbb09cece8d1791fa6d967fe57067137a8cff` |
| Local `origin/main`, entry and exit | `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0` |
| Ahead / behind | 4 / 0, unchanged |
| Staged state | Empty, entry and exit |
| Historical files fingerprinted | 96; all unchanged at exit |
| Existing tracked-file contents | No changes between detailed entry and exit snapshots |
| Live Echo | PID 71538, PPID 56610; started Sept 28, 19:15:54 PDT; same process afterward |
| Echo resource tracker | PID 71548, unchanged |
| Ollama server | PID 1991; started Sept 19, 10:57:03 PDT; unchanged |
| Live remote verification | **Unavailable:** approved read-only `git ls-remote` reached GitHub but failed public-key authentication |

The initial short status contained existing modifications to `CLAUDE.md`, `PENDING_DECISIONS.md`, three `app/core` files, relay cursor/message files, `logs/janitor_report.json`, `sandbox/scripts/temp_self_edit.py`, and `staging/self_edit_candidate.py`, plus substantial untracked research. These were not assumed to be this mission's work. Full expanded status and hashes are in [entry_provenance.json](../memory/experiments/equality_localization/20260929_codex_v1/entry_provenance.json) and [exit_integrity.json](../memory/experiments/equality_localization/20260929_codex_v1/exit_integrity.json).

No push was issued by this mission. An unchanged cached `origin/main` is **not proof that no other actor pushed remotely**; that requested global check remains unverified because authentication failed. No credentials or alternative authentication paths were sought.

Concurrent Claude work was preserved. Its structural-prior and stage-localization files were not read substantively until after the independent provisional localization was frozen. No relay message, LaunchAgent action, production restart, VSL access/promotion, or production memory operation was performed.

New files are isolated to [diagnostic.py](../app/experiments/equality_localization/diagnostic.py), this report, and [the forensic evidence directory](../memory/experiments/equality_localization/20260929_codex_v1/). A final [artifact manifest](../memory/experiments/equality_localization/20260929_codex_v1/artifact_manifest.json) enumerates the exact created files. All are additive; none replaces another investigator's evidence.

## 2. Three-failure reconstruction

Primary historical source:

- [design.py](../app/experiments/counterfactual_acquisition/design.py): world creation, target function, grammar, prompt assembly.
- [worker.py](../app/experiments/counterfactual_acquisition/worker.py): exact API request construction and fresh-process policy consumption.
- [policy.py](../app/experiments/counterfactual_acquisition/policy.py): parsing, validation, execution, comparison.
- [controller.py](../app/experiments/counterfactual_acquisition/controller.py): response extraction, retained state, request/state hashing, qualification scoring.

The complete newly reconstructed traces are in [historical_traces.json](../memory/experiments/equality_localization/20260929_codex_v1/historical_traces.json). They preserve exact model-facing messages, raw response text, parsed objects, canonical serialization, state content, truth tables, saved outputs, and source-file fingerprints.

| Historical failure | World seed | Relevant features | Orientation / side | Raw response policy | Independently correct |
|---|---:|---|---|---|---:|
| `dev_0_oracle_1` | 910421 | 2,4 | 0 / 1 | `AND(feature 2, feature 4)` | 48/64 |
| `dev_1_oracle_1` | 910422 | 2,3 | 0 / 1 | `AND(feature 2, feature 3)` | 48/64 |
| `dev_2_oracle_1` | 910423 | 3,5 | 0 / 1 | `AND(feature 3, feature 5)` | 48/64 |

Each trace follows the same verified chain:

| Boundary | Actual artifact or operation | Still equality? |
|---|---|---|
| World | Original seed reconstructs the saved history exactly | Yes, for orientation 0 / side 1 |
| Intended target | `(xi + xj + orientation + side) % 2 == 1` | Yes, by independent truth table |
| Model-visible rule | “target is true exactly when feature i and feature j are equal; otherwise false” | Yes |
| Request | Saved system/user messages match reconstruction; request digest matches worker and controller records | Yes |
| Raw response | `response.message.content` contains `["and",["feature",i],["feature",j]]` | **No: first observed AND** |
| Parsed object | JSON parsed and AST validated; same `and` node | AND preserved |
| State | Exact raw response string stored as `raw_policy`; state digest matches consumer | AND preserved |
| Canonical JSON | Changes formatting/key order only; reparsing gives identical AST | AND preserved |
| Execution | Every saved output matches independently executed AND | AND preserved |
| Grading | Both-zero inputs fail; other inputs pass | Correctly measures the wrong policy |

Exact historical request/response files are under [the original calls directory](../memory/experiments/counterfactual_acquisition/20260929_resume_v1/calls/), named `dev_0_oracle_1`, `dev_1_oracle_1`, and `dev_2_oracle_1`, with `.request.json` and `.response.json` suffixes. The original state paths and hashes are retained in the trace records.

The repaired-ledger repeat used identical request bytes and returned identical policy strings for all six privileged calls, not just the three failures. This was rechecked from those files, not inferred from the report. The repaired ledgers' 28 events independently rehash and link correctly. See [historical_repetition_and_integrity.json](../memory/experiments/equality_localization/20260929_codex_v1/historical_repetition_and_integrity.json). The old hash-field problem cannot explain a substitution already visible in the raw API response.

## 3. What the worlds actually require

No model answer or final score is needed to derive the target. For every original failure, orientation=0 and side=1. Thus the target is true when the relevant bits sum to 0 or 2, and false when they sum to 1.

| A | B | Equality / equivalence | AND | DIFFERENT / XOR |
|---:|---:|---:|---:|---:|
| 0 | 0 | true | false | false |
| 0 | 1 | false | false | true |
| 1 | 0 | false | false | true |
| 1 | 1 | true | true | false |

The smallest distinguishing witness is the all-zero six-feature vector. For every relevant pair here:

```text
x = [0,0,0,0,0,0]
equality target = true
AND output      = false
```

The four irrelevant features have 16 combinations. Consequently, exactly 16 of 64 vectors have both relevant bits zero, causing exactly 25% error and the observed 75% accuracy. This is the complete explanation of the score, not a sampling estimate.

**Information distinction:** the original 16 record entries all had `feedback="WITHHELD"`. Their attempted actions are not verified labels. Those records alone do not imply equality or any competing relation. Equality is justified by the protected world definition and explicitly communicated to the model by the privileged sentence. Any interpretation that the original model first had to infer equality from evaluated examples is inaccurate for these calls.

## 4. Whether the DSL can represent equality

**Yes, without modification.** The language has Boolean constants, feature leaves, unary NOT, and binary AND, OR, XOR. It has no direct EQUAL/XNOR primitive. Equality is expressible compositionally.

Three equivalent expressions were checked for each actual feature pair:

```json
{"policy":["not",["xor",["feature",2],["feature",4]]]}
```

```json
{"policy":["xor",["feature",2],["not",["feature",4]]]}
```

```json
{"policy":["or",["and",["feature",2],["feature",4]],["and",["not",["feature",2]],["not",["feature",4]]]]}
```

The other worlds substitute pairs (2,3) and (3,5). All nine correct expressions passed all 64 inputs. Three deliberately incorrect AND expressions produced 48/64, preserving the crucial negative control.

The parser allows these compositions directly; there is no normalization pass that rewrites equality to conjunction, and no special prohibited equality form. Bounds are 8,192 response bytes, 63 AST nodes, and depth 8. The shortest equality expressions are far inside those limits.

**E1 — representational capacity failure is rejected for this DSL and task.** No primitive was added.

## 5. Whether parser/executor preserve equality

The forensic driver performed **12 fresh-process manual-policy tests**: three equality forms plus one AND negative control in each of the three historical worlds.

For every test:

1. Construct a clearly labeled manual diagnostic expression.
2. Serialize it as formatted JSON.
3. Pass it through the unchanged `parse_policy()` validator.
4. Serialize the validated object through the existing canonical JSON function and reparse it.
5. Verify the AST remains exactly equal to the constructed object.
6. Store the raw expression in an isolated diagnostic state file and hash it.
7. Invoke the unchanged consumer in a fresh Python process with only state path/hash and the 64 inputs.
8. Preserve process stdout/stderr immediately.
9. Compare every returned output against a separate evaluator written for this forensic review and the independent equality truth table.

All checks agreed. [manual_semantic_witnesses.json](../memory/experiments/equality_localization/20260929_codex_v1/manual_semantic_witnesses.json) identifies every expression, state hash, process record, structural size, and score; [manual/](../memory/experiments/equality_localization/20260929_codex_v1/manual/) contains the exact requests and process outputs.

These hand-written policies are **measurement witnesses**, not acquired states or replacement answers for qualification. They were never fed to the model as demonstrations. No policy was promoted or substituted for a failed generated policy.

## 6. Whether the evaluator scores equality correctly

**Yes on all tested worlds and complete input domains.** All nine manual equality policies scored 64/64; all three manual AND controls scored 48/64. Raw historical policies independently reconstruct to precisely the saved outputs and scores.

The trusted controller compares strict Boolean outputs with expected values. The closed DSL cannot execute Python, read expected arrays, access the filesystem, or reinterpret a verdict marker. The consumer does not receive the expected values.

There is no demonstrated parser, state serialization, execution, or comparison corruption. **E2 is rejected for these actual paths.** This bounded result does not claim general security of arbitrary Python execution or validate unrelated evaluators.

## 7. Whether the model identifies equality conceptually

**Not in the three new probes. No correct conceptual intermediate was observed.**

The model-facing conceptual task deliberately omitted DSL syntax, policy generation, library entries, prior outputs, and relation-choice labels. The correct feature pair was supplied so this did not repeat Claude's feature-selection experiment. Each prompt used the same 16 input vectors from its historical case, with independently reconstructed `target` values in place of the original attempted/WITHHELD records.

The common request asked for an ordinary-language relationship description and four Boolean predictions. It contained no worked derivation or named equality answer. The four probe vectors had the relevant values 00,01,10,11, with other features zero. Correct behavior was prospectively defined as `[true,false,false,true]`; a label alone was insufficient.

**This condition is richer than the original records.** It tests relation inference from direct observations, not the original task of reading an explicit equality sentence. It cannot recover an unobserved historical thought state. All four relevant input combinations are represented in each observation set, with counts:

| World / pair | 00 | 01 | 10 | 11 |
|---|---:|---:|---:|---:|
| 0 / (2,4) | 4 | 8 | 2 | 2 |
| 1 / (2,3) | 5 | 2 | 5 | 4 |
| 2 / (3,5) | 3 | 3 | 8 | 2 |

Raw results, in probe order 00,01,10,11:

| Probe | Exact `relation` text | Predictions | Prediction semantics over these four rows | Correct /4 |
|---|---|---|---|---:|
| World 0 | “The target is true if feature 2 is 1 and feature 4 is 1.” | false, true, true, false | DIFFERENT/XOR | 0/4 |
| World 1 | “The target is true when feature 2 is 1 and feature 3 is 0.” | false, true, true, true | OR | 1/4 |
| World 2 | “The target is true if feature 3 is 1 and feature 5 is 0.” | false, false, true, false | A AND NOT B | 1/4 |

World 0 **says AND but predicts XOR**. World 1 describes A AND NOT B but predicts OR. World 2's text agrees with its predictions, but both are wrong for equality. These inconsistencies are why a self-reported relationship cannot be accepted as proof of conceptual understanding.

All three predict false on 00, the same distinguishing row missed by the historical AND policies, but their other errors differ. That overlap suggests a possible shared weakness; it does not establish a common internal mechanism or an equality-specific deficit. There was no matched no-DSL non-equality concept task in this small diagnostic.

This supports **E3 as an operational pre-DSL diagnostic failure**. It does not isolate abstract relation knowledge from reading six-position arrays, binding feature indices, extracting labels, or obeying a new output request. Those operations still occur inside the same model call.

## 8. Whether EQUAL → DSL translation succeeds

Under the **original explicit-equality request**, it fails. The fresh anchor request was identical to `dev_0_oracle_1`, including model settings and seed. It again returned:

```json
{
  "policy": ["and", ["feature", 2], ["feature", 4]]
}
```

Independent execution and the unchanged consumer agreed on AND, 48/64 against equality. Inference of the rule was already unnecessary in this original prompt: the relation and feature pair were supplied explicitly. Thus **giving the correct relation does not prevent the observed failure**.

The new minimal `EQUAL` label-to-DSL request was frozen but **not executed**. The plan required at least one conceptual probe to demonstrate equality behavior before proceeding to the new translation triplet. None did. A failed prerequisite was not reworded or bypassed after observing results.

Consequently, there is no new evidence here that the model first recognized equality correctly and then lost it specifically during encoding. **E4 is not established.** The historical and fresh-anchor evidence establishes a specification-to-output error across the model-service interface, a broader statement.

## 9. DIFFERENT control result

Existing qualification evidence supplies the relevant control without another model experiment. For pairs (2,4), (2,3), and (3,5), the original `different` sentence produced exact XOR policies, 64/64. The repaired-ledger repeat returned the same requests and outputs, again 64/64.

Those six calls are three matched requests repeated, not six independent task families. They show that the original API/grammar/output/execution path can produce the correct direct binary relation under these conditions.

The fresh minimal `DIFFERENT` probe was skipped with the rest of the conditional triplet. No result is imputed to it. The contrast between historical EQUAL failure and DIFFERENT success is real, but does not by itself identify whether relation comprehension, compositional encoding, lexical associations, or context accounts for the asymmetry.

## 10. Whether EQUAL and AND collapse during translation

The historical and fresh original-context **EQUAL requests produce the AND function**. That functional substitution is established, not merely suggested by an operator name.

A stronger claim that explicit `EQUAL` and explicit `AND` labels produce identical policies under an otherwise identical minimal prompt is **not tested here**. The frozen `AND` control was skipped after the conceptual gate failed. Manual AND witnesses validate its meaning, but are not model-generated AND controls.

Nor can the first conceptual probe's AND description establish an internal AND representation: its accompanying predictions implement XOR. Textual labeling and demonstrated behavior must remain separate.

## 11. Relevant prompt/context biases

The complete original requests are preserved in the trace artifact and original call files. Their order is:

1. System instruction: “You are the local FeralEcho experimental learner. Infer from supplied evaluated experience. Return only the requested JSON policy.”
2. Six-feature deterministic-device task and PASS/FAIL/WITHHELD definitions.
3. Grammar, bounds, and output-only requirement.
4. Generic sentence saying the actual rule is not supplied by that description.
5. Explicit external oracle sentence supplying the feature pair and equality relation.
6. Sixteen attempted actions, all feedback WITHHELD.

The exact grammar includes:

```text
true or false; ["feature",i] where i is 0 through 5; ["not",expr];
["and",expr,expr]; ["or",expr,expr]; ["xor",expr,expr].
```

**Absent:** prior policies, worked Boolean-policy demonstrations, De Morgan examples, verified-skill library blocks, earlier assistant turns, retrieval results, VSL content, and tools. The explicit model request has just system and user messages. There is no DSL semantic normalization between the request and the response.

Plausible but unproven influences:

- Equality has no named primitive; AND and XOR do. A correct equality answer requires composition.
- Operator meanings are conventionally named, not explained with full truth tables. AND appears before OR and XOR in the grammar.
- “Feature i and feature j are equal” contains the ordinary conjunction word `and`; however the successful `different` sentence contains that word too, so lexical occurrence alone is not a sufficient explanation.
- Generic “infer from experience” framing and the sentence about an unspecified rule coexist with a later explicit rule. This may impose an instruction-selection burden; it is not demonstrated prompt corruption.
- WITHHELD records follow the useful rule and can distract or be misread as demonstrations. Attempted actions are not targets. If wrongly treated as targets, their agreement with equality versus AND is 10/16 vs10/16, 9/16 vs10/16, and 3/16 vs6/16 across the three worlds. That descriptive pattern does not prove the model used them that way.

Current Ollama `/api/show` metadata was preserved in [model_show_at_run.json](../memory/experiments/equality_localization/20260929_codex_v1/model_show_at_run.json). It reports a generic Qwen system string and message-format template, with no stored example messages or task-specific library. Tool-template text is conditional; these requests supply no tools. This provides no positive evidence of hidden skill-library injection. Exact flattened runtime tokens and hidden activations were not captured, so this is not omniscient verification of model internals.

## 12. Representation-complexity comparison

Counts use the project's AST convention: a feature leaf is one node; depth starts at zero. Byte counts include the compact `{"policy":...}` JSON wrapper, for one-digit feature indices.

| Function / representation | Nodes | Maximum depth | Boolean operators | Compact bytes |
|---|---:|---:|---:|---:|
| AND(A,B) | 3 | 1 | 1 | 46 |
| XOR(A,B) | 3 | 1 | 1 | 46 |
| NOT(XOR(A,B)) | 4 | 2 | 2 | 54 |
| XOR(A,NOT(B)) | 4 | 2 | 2 | 54 |
| OR(AND(A,B),AND(NOT(A),NOT(B))) | 9 | 3 | 5 | 105 |

An independent exhaustive enumeration of all expressions of at most three nodes, using all six feature leaves, both constants, and the existing operators, found no equality representation. There were 8 one-node, 8 two-node, and 200 three-node expressions counted with syntactic duplicates. The four-node witnesses show that four is sufficient. See [minimal_ast_capacity.json](../memory/experiments/equality_localization/20260929_codex_v1/minimal_ast_capacity.json).

Equality therefore has a real but small compositional disadvantage: one additional node/operator and eight compact bytes in its shortest form. The original 22-token responses ended normally, far below the 768-token generation limit. This is not an observed hard budget or grammar-bound failure.

**E6 remains a candidate**, not an identified cause. There was no intervention on complexity independent of relation meaning, no operator-order randomization, and no demonstration that a correctly understood equality relation was compressed into AND. The new pre-DSL failures also cannot be explained solely by AST size.

## 13. Context-ablation result and frozen diagnostic accounting

**The context ablation was not reached.** Its prerequisite was a correct conceptual probe plus a failed full-context anchor. The anchor failed, but none of the conceptual probes was correct.

The frozen ablation would have replaced only the original 16 WITHHELD records with `[]`, retaining the original system message, grammar, oracle sentence, options, seed, and record-section heading. That exact request is preserved but has no observed response. No alternate prompt was tried instead.

The [diagnostic plan](../memory/experiments/equality_localization/20260929_codex_v1/diagnostic_plan_frozen.json) was frozen before model calls, with exact requests, conditional gates, model identity, source hashes, E0–E8 dispositions, and no-retry rules. SHA-256:

`c2e8c8c49d4c368a0fd1fd435f05bb82fa1d2f7e39f59403c129ea4d915f4d3c`

| Scheduled diagnostic | Result |
|---|---|
| Original equality anchor | Completed; AND, 48/64 |
| Concept world 0 | Completed; equality behavior failed |
| Concept world 1 | Completed; equality behavior failed |
| Concept world 2 | Completed; equality behavior failed |
| Minimal EQUAL translation | Skipped by frozen gate |
| Minimal DIFFERENT translation | Skipped by frozen gate |
| Minimal AND translation | Skipped by frozen gate |
| Original context minus WITHHELD records | Skipped by frozen gate |

Four model calls completed; zero model-call errors, timeouts, retries, or length terminations. The anchor took 75.390 seconds, including 65.673 seconds reported load duration. Concept calls took approximately 7.004, 6.978, and 7.342 seconds. All completed with `done_reason=stop`. The anchor used 661 prompt /22 output tokens; each conceptual probe used 464/40. Options remained temperature 0, top_p 1, output budget 768, context budget 4096; conceptual seeds were 813000–813002, matching their original worlds.

The reported model was `qwen2.5-coder:7b`, registry digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`, Ollama 0.34.2. Identity was checked before calls. The shared backend was not reset or otherwise controlled beyond these requests.

Every executed request, raw process stdout/stderr, and interpreted result was saved immediately in [requests/](../memory/experiments/equality_localization/20260929_codex_v1/requests/), [processes/](../memory/experiments/equality_localization/20260929_codex_v1/processes/), and [results/](../memory/experiments/equality_localization/20260929_codex_v1/results/). [diagnostic_results.json](../memory/experiments/equality_localization/20260929_codex_v1/diagnostic_results.json) includes all four conditional skips. There were no post-freeze deviations. The explicit information change in conceptual probes was declared before execution, not concealed as a reproduction of the original WITHHELD evidence.

## 14. Structural-prior interaction

**Not tested.** The original qualification context has no prior structural skill examples. The mission's condition for constructing a library-crossed equality diagnostic was therefore not met. No XOR-heavy or AND/OR/NOT-heavy library was introduced, and Claude's experiment was not duplicated.

The observed failure does not require an explicit library: it occurs in library-free original requests and the fresh anchor. That does not show structural context could never change translation, nor does it exclude pretrained structural priors or effects of the common grammar. It rules out a specific claim that a prior verified-skill library in these actual requests caused the historical substitution.

## 15. Earliest localized failure and dispositions

**Historical path:** correct external equality specification → model-service generation → raw AND response. This is the narrowest source-supported location. There is no recorded intermediate conceptual representation inside the original generation. The API/template/backend/decoder segment is not instrumented finely enough to assign the error to a particular hidden computation.

**New diagnostic path:** direct verified observations plus supplied feature pair → wrong ordinary-language description and/or four-row predictions, before requesting any DSL. A pre-DSL failure is demonstrated in these new conditions, but it is not a captured internal stage of the historical call.

| Pre-registered disposition | Evidence judgment |
|---|---|
| E0 — world/specification error | Not supported: world, independent truth table, and original explicit sentence agree. |
| E1 — DSL capacity failure | Rejected: multiple accepted equality expressions work on all worlds. |
| E2 — parser/executor corruption | Rejected for tested paths: AST, raw state, execution, and grading preserve semantics. |
| E3 — conceptual relation failure | **Observed in the new no-DSL diagnostic**, with supplied features and direct labels. Do not equate this with knowledge of the original hidden state. |
| E4 — concept-to-DSL translation failure | **Not established as loss of a correctly recognized concept.** Explicit equality specification-to-DSL failure is established, which is weaker. |
| E5 — context-induced representation bias | Unresolved; planned ablation skipped and no original library present. |
| E6 — simplicity bias candidate | Compatible with structural asymmetry; no causal test or proof. |
| E7 — multiple failures | Multiple output error shapes occur; independent internal defects are not identified. |
| E8 — no localization | Applies to the **remaining model-internal distinction**, not to the already localized request/response boundary. |

The old characterization “policy representation failure” is defensible as a description of the wrong representation produced. It should not be upgraded to the mechanistic claim “the model first understood equality and then failed only at encoding.” The new evidence provides no such correctly understood intermediate.

## 16. Relationship to Claude's parallel findings

The independent provisional result was frozen **before reading Claude's new reports** in [provisional_localization_frozen.json](../memory/experiments/equality_localization/20260929_codex_v1/provisional_localization_frozen.json), SHA-256:

`5a1e1842d003a4872cf2070b61599887faba762139f434b96f23e1b72d5da492`

Only afterward were [Claude's relational-stage report](2026-09-29_relational_hypothesis_stage_localization.md), [structural-prior report](2026-09-29_structural_prior_test.md), their relevant scripts, saved requests, raw responses, and result JSON inspected. The comparison evidence and hashes are preserved in [claude_comparison_primary_evidence.json](../memory/experiments/equality_localization/20260929_codex_v1/claude_comparison_primary_evidence.json).

**Convergence:** Claude's true-equality conceptual conditions X, D, and N all returned the label DIFFERENT for pair (0,5). Independent decoding of its PASS/FAIL records confirms that the supplied evidence actually requires equality. Those errors occur without requesting a DSL policy. My probes also fail before DSL, on three other historical feature pairs, with direct target observations rather than a PASS/FAIL decoding requirement. Neither investigation supports assuming a reliably correct conceptual intermediate.

**Distinct information conditions:** Claude asks for one of EQUAL/DIFFERENT/OTHER from evaluated episodes. My conceptual probes ask for free descriptions plus actual predictions from direct labeled observations. The original qualification explicitly supplies equality in language and asks for policy code. These are not a mechanically observed chain of internal model stages.

**Substantive disagreement:** Claude's categorical statement that the original equality→AND failure is localized to “Stage 2” is too strong. Its report also acknowledges the key limitation: DIFFERENT is the opposite of equality, whereas AND agrees on three of four rows, and the experiments may concern related but distinct failures. I accept the demonstrated new pre-DSL error, while retaining the unresolved distinction between comprehension and encoding in the original supplied-rule calls. Later conceptual errors cannot retroactively expose the original model's hidden intermediate state.

**Feature selection:** Claude's saved Stage-1 outputs omit one of the two true features in every condition. That is a separate observation. In my original failing policies, both supplied feature indices are correct. My new conceptual task supplies the pair and does not test discovery of relevant features, so it neither replicates nor refutes that finding.

**Structural-prior scope:** the cited 100% XOR-family rate covers **3/3 valid** X generations; a fourth X generation was syntactically invalid. D and N each have 4/4 valid AND/OR/NOT-family outputs. This is operator occupancy, not semantic correctness, and does not show why a supplied equality concept becomes AND in requests containing no library.

One additional matching limitation surfaced in the required source comparison: saved library-condition requests use **different sampling seeds**. Phase 8 uses X/D/N seeds 861001/861002/861003; Phase 9 Stage 1 uses 871001/871002/871003. Equality Stage-2 seeds are 871013/871014/871015. Thus “only library content differs, including identical seed” is not literally true of these artifacts. Temperature zero may make seed differences immaterial, but a same-request repeat at one seed does not establish that experimentally across seeds. This is a qualification of the strong causal wording, not proof that seed differences caused the observed library association. No new test or repair was performed.

The raw findings were not altered to match Claude. The investigations converge on demonstrated weaknesses; neither proves a single common internal mechanism.

## 17. Confidence and limitations

**High confidence:** the actual worlds require equality; the first visible AND is in the raw response; both feature indices are correct there; serialization and downstream execution preserve that response; the DSL represents equality; manual equality policies score correctly; the original requests contain no skill library; the fresh original-context call reproduces AND.

**Bounded empirical confidence:** the three specific conceptual calls fail and two text descriptions contradict their predictions. This is more informative than accepting a self-report label. It is not a population estimate of model conceptual competence or a proof of a dedicated internal “relation” module failure.

**Unresolved:** exact hidden recognition state during the original generation; whether the explicit equality phrase was misunderstood versus correctly understood but incorrectly encoded; effects of original non-library context; comparative minimal EQUAL/AND translation; abstract simplicity bias; any common cause with Claude's feature-selection results.

There is one output per new condition, no balanced relation-control concept dataset, and no hidden activation access. Conceptual observations are deliberately easier to read than original evaluated-attempt feedback, yet are not identical to the original privileged-instruction condition. No nominal binomial significance claim is made from correlated truth-table rows. Backend caching/scheduling was not fully instrumented, and the local service was shared with other work.

The original new-world timeout remains untouched and incomplete. This mission had no timeouts. The prior main qualification threshold was neither re-evaluated for authorization nor changed. The diagnostic's manual gold expressions cannot close that gate.

Integrity at the final snapshot: HEAD and local tracking ref unchanged; no staged files; all 96 protected files unchanged; no existing tracked contents changed. Production PIDs/start times unchanged. Only this forensic driver, evidence, and report were created. No main learner, acquisition protocol, revision procedure, VSL promotion, production edit, process restart, commit, push, or LaunchAgent activation occurred.

## 18. Recommended next action and explicit answers

**One next action, requiring separate authorization:** review a narrowly matched comprehension probe that keeps the original explicit oracle sentence and context but asks only for the four target truth values, with no DSL and no newly labeled examples. It would test comprehension of the **same supplied specification**, avoiding the current gap between evidence-based conceptual inference and instruction-to-code generation. Do not change the language, prompts in the existing apparatus, or qualification gate to implement a repair. No such additional probe was run here after the frozen gate failed.

**Does the model know the relationship is equality before it writes policy code?**

Not established. All three no-DSL diagnostic predictions fail equality. The original model's hidden conceptual state is unavailable; receiving the word `equal` is not evidence that it was understood.

**If yes, at exactly what boundary does equality become AND?**

The premise “if yes” was not demonstrated. At the observable interface, the request still specifies equality and the raw response already specifies AND. Nothing downstream introduces the substitution.

**Can the existing DSL represent equality correctly without modification?**

Yes: NOT(XOR), XOR(A,NOT(B)), and a both-same AND/OR/NOT composition all work.

**Does a manually correct equality policy survive parsing, execution, and evaluation unchanged?**

Yes. Nine correct manual policies across the three worlds preserved their AST semantics and each scored 64/64. Three AND controls each scored 48/64.

**Does the equality failure persist when inference is removed and the model is explicitly told the intended relation is EQUAL?**

Yes under the original explicit-equality wording and context: the fresh identical request again returns AND. The separate minimal uppercase-EQUAL translation condition was not reached, so no result is claimed for it.

**Does structural/library context alter that translation?**

Unknown. There was no original library to ablate; a library-crossed explicit-equality translation experiment was not run. Claude's library experiments address different tasks and do not supply that missing comparison.

**Is equality→AND primarily an inference failure, a representation/translation failure, a context-induced bias, an implementation defect, or still unresolved?**

It is a reproducible **model-generation semantic failure**, with the downstream implementation provisionally exonerated. Pre-DSL errors are independently demonstrated, but the original failure is **still unresolved between comprehension/inference and encoding**, with context and simplicity explanations untested. The evidence does not justify protecting a pure translation-failure story—or replacing it with a proven common inference mechanism.

**No repair performed. No further experiment authorized by this report.**
