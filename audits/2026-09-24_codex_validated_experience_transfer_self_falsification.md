# Independent attempt to falsify Codex's VECT critique

Date: 2026-09-24 (America/Los_Angeles). Investigator: Codex. Read-only forensic review; no model calls, candidate executions, learning trials, repairs, or replacement evidence.

## 1. Executive verdict

**B. MY ORIGINAL CRITIQUE WAS PARTLY WRONG / TOO STRONG.**

There is stronger evidence of reusable behavior than my earlier assessment credited. There is still no demonstrated Echo-operated extraction of the retained lesson.

The most important correction is concrete: **six P-arm records contain byte-identical executable source, successfully evaluated on six different inputs spanning three code-opening categories.** Another identical-source group passes three inputs. All ten P outputs implement the same general line-boundary extraction algorithm. These are not ten hardcoded answers. The preserved code supports a source-derived generality argument beyond the ten inputs, subject to the generator's restricted assumptions.

The evaluation also contains genuine compositional novelty: every complete input and every combination of code category, prose-type layout, and separator count differs from TRAIN. Six evaluation inputs have prose-type layouts absent from TRAIN. My earlier emphasis on repeated code bodies understated that the task is boundary extraction, for which new arrangements can be meaningful new cases.

However:

- The same four exact code snippets occur in both TRAIN and evaluation. There is no held-out program content or new task family.
- Every generation prompt contains its eventual grading input. No prospective test of one frozen candidate against additional concealed inputs was found.
- The procedure-freezing script writes an investigator-authored literal. It verifies cited episode identifiers, not an automatic inference from outcomes. Echo's local worker produced relevant precursor solutions and failures, but did not demonstrably perform the cross-episode lesson extraction.
- The numerical result remains P 10/10, G 6/10, Z 5/10. The paired one-sided P–G p-value remains 0.0625. All four P–G wins are variants of the same docstring-containing snippet.

**The narrow positive result is stronger than “instructions were stored,” but weaker than “Echo autonomously acquired competence from its own experience.”** Persisted external guidance was consumed in fresh model contexts and accompanied reusable, more successful code on a small panel of newly combined inputs. A fixed pretrained model plus an externally supplied task-specific lesson still explains every surviving observation.

“Not demonstrated” here is not a claim that frozen weights preclude system learning.

## 2. Evidence searched and integrity

**OBSERVED.** Opening and closing HEAD: 2fba42644c82b9f7096276f4dd338d615cf1bcce. Branch main, 17 commits ahead of origin/main. Opening working tree contained **28 modified tracked entries and 349 untracked file entries**. These predated this investigation.

The pre-existing tracked changes included CLAUDE.md, PENDING_DECISIONS.md, eleven app/core files, app/emergent_scheduler.py, app/maintenance/night_cycle.py, an older audit, four claude_relay files, logs/janitor_report.json, research/OPEN_QUESTIONS.md, run.py, two sandbox files, two verification scripts, and staging/self_edit_candidate.py. They were not cleaned, reset, repaired, or overwritten.

A 32-file byte-hash manifest was captured at 2026-09-25T04:46:44.039332Z and checked again at 2026-09-25T04:56:29.223550Z before report creation. **All 32 hashes matched; HEAD and the complete porcelain-v2 working-tree listing also matched.** Final verification after report creation is recorded below. Git status alone does not cover ignored experimental memory, which is why the evidence files were separately hashed.

### Primary source map

All paths below are relative to the repository root unless linked.

| ID | Evidence | Use |
|---|---|---|
| V1 | [VECT run.py](/Users/richietate/Desktop/FeralEcho/app/experiments/validated_experience_competence_transfer/run.py:69) | Task sealing, TRAIN attempts/retries, treatment loading, held-out calls and grading |
| V2 | [freeze_procedure.py](/Users/richietate/Desktop/FeralEcho/app/experiments/validated_experience_competence_transfer/freeze_procedure.py:35) | Actual lesson writer and provenance check |
| V3 | [prompt.py](/Users/richietate/Desktop/FeralEcho/app/experiments/validated_experience_competence_transfer/prompt.py:15) | Candidate-visible information |
| V4 | [CONTRACT.md](/Users/richietate/Desktop/FeralEcho/app/experiments/validated_experience_competence_transfer/CONTRACT.md:1) | Declared design, analysis, investigator extraction, ordering |
| V5 | [generator tasks.py](/Users/richietate/Desktop/FeralEcho/app/experiments/historical_difficulty_calibration/tasks.py:44) | Fixed content banks, procedural combinations, task description |
| V6 | [standalone sandbox.py](/Users/richietate/Desktop/FeralEcho/app/experiments/minimal_procedure_transfer/sandbox.py:69) | Actual extraction, execution and exact-match grader |
| V7 | [standalone ollama_client.py](/Users/richietate/Desktop/FeralEcho/app/experiments/minimal_procedure_transfer/ollama_client.py:45) | Requested model, sampling and fresh message construction |
| V8 | memory/experiments/validated_experience_competence_transfer/{train_tasks.json, experience_log.jsonl, procedure_frozen.json, procedure_hash.txt} | Executed experience and retained state |
| V9 | Same directory: {heldout_tasks.json, heldout_results.jsonl, heldout_commitment.sha256, generic_tip_treatment.json} | Executed evaluation, outcomes and controls |
| V10 | VECT freeze_generic_tip.py and consumption_signatures.py | G authorship and static consumption detectors |
| H1 | historical_difficulty_calibration/{run_calibration.py,evaluator_qualification.py}; corresponding recorded calibration results | Earlier task qualification, native capability and headroom |
| H2 | minimal_procedure_transfer/baseline_results.jsonl; corresponding experiment source/report | Earlier baseline ceiling and unrun transfer branch |
| H3 | first_learning_loop/{lesson_mining.py,harness.py,v1_2_clean_transfer.py,trial_results.jsonl,v1_2_trial_results.jsonl} | Actual automated historical extraction and transfer attempts |
| H4 | architecture_a_hot_stove_proof/{harness.py,run_experiment.py,trial_results.jsonl,candidate_knowledge.jsonl,run_report.json} | Failure-derived retry-context comparison |
| H5 | scripts/validate_behavioral_state_live.py; audits/c1_live_validation_raw_results.jsonl; app/core/{behavioral_state.py,echo_ground_truth.py} | Durable external directive and fresh-process consumption |
| H6 | app/experiments/learning/{harness.py,prompts.py,scoring.py}; scripts/run_learning_investigation_pilot.py; memory/experiments/learning/trials.jsonl | Existing retention/retrieval/ablation pilot |
| H7 | scripts/memory_ablation_results_2026-07-23.json; scripts/memory_ablation_results_nonpersonal_2026-09-03.json; associated drivers | Memory-dependent behavior versus measured correctness |

The September 23 VECT report and calibration report were used as maps and checked against these artifacts. Repository searches also checked for later consumers of the VECT procedure, secondary grading, additional result files and relevant Git history. No tracked history was returned for the VECT source/report paths: these additions are untracked at this HEAD. That limits reconstruction of historical code versions.

I did not open unused sealed AP-0 Stage 1 tasks, the unrun minimal-transfer held-out corpus, or unrelated sealed experimental stimuli. No repository modules were imported for verification. Calculations used standard-library JSON, hashing, AST inspection, counting and exact binomial arithmetic; no generated candidate was executed.

### Integrity qualifications

- The procedure's canonical JSON hash is **21fde9b5dbe026489ef8f3ff47f974c816ca706944cde251b2501ed7f541f3c8** and matches procedure_hash.txt.
- The executed held-out corpus's canonical JSON hash is **a35c0807cc505ed4d192b44f17b2705427ccf8e3a46af374557e60d9a8c90055** and matches heldout_commitment.sha256.
- Canonical-object hashes intentionally differ from hashes of indented file bytes.
- V1 discloses a path correction after sealing/TRAIN: output was initially written outside the repository and moved into the intended directory. Current hashes are consistent with the preserved corpus. They do not independently prove every historical move or absence of reads.
- A hash commitment prevents undetected changes relative to that commitment; it does not prove that the investigator could not inspect the already-created held-out file.

**A timestamp discrepancy matters for accurate reconstruction.** The retained JSON records P frozen at **2026-09-24T10:56:07Z**, and G at **10:57:19Z**. The report labels corresponding local PDT times 03:56:07 and 03:57:19 with a Z suffix. Its date is September 23, but these executions were September 24, including in local time. File metadata supports TRAIN ending around 10:52:22Z and held-out records spanning approximately 10:58:23–11:00:10Z. The seven-hour labeling error does not reverse the ordering. File timestamps are supporting evidence, not immutable third-party attestation.

**A separate preregistration limitation:** the current consumption-signature file was modified after held-out results. The report discloses widening the anchoring detector after inspecting output, while also describing the checks as predeclared. I found no independently frozen original detector version. Treat the corrected signatures as diagnostic evidence; do not use their current file as proof of an unchanged prospective instrument.

<details>
<summary>32-file byte-SHA-256 manifest captured before analysis and verified afterward</summary>

| File | SHA-256 |
|---|---|
| app/core/behavioral_state.py | 6c50f6b7ee9cfd4ca8fb9261be72c6706a05a08f78b0793a161598290871b130 |
| app/core/echo_ground_truth.py | 9b78bd9ed91c61da72dddcba543979bc5ba717ddd2b04ef75d57e5a648979005 |
| app/core/river_deliberation.py | 5d1aa77911509ebbc90d01cd084e5ac3b4c8bd7b9790bc2780b5ce226c253585 |
| app/core/self_edit_manager.py | e698ab0fbbea5ffde0b14e2806260aa1dc0f1d7cd9af882912683bfdfe5334b9 |
| app/core/self_model_claims.py | 40036a4170270bc4d9b05bdbc3432cc1587cd626e9d80498aeb719c8b31e3da5 |
| app/experiments/historical_difficulty_calibration/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/experiments/historical_difficulty_calibration/evaluator_qualification.py | 7627649d69e99e8736e27e441a6f0e881a261b30ae45cc00a3941b71a28ef909 |
| app/experiments/historical_difficulty_calibration/run_calibration.py | a2a9a4bb22b2579aeac8396b9ed0970763f0bd5972ebacae6ec875d349c7e8ff |
| app/experiments/historical_difficulty_calibration/tasks.py | 6da0d62bb575f6e10a08c6bdf23b8e50d7c0ac6cf7dfd33f083405279bb17a2b |
| app/experiments/minimal_procedure_transfer/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/experiments/minimal_procedure_transfer/ollama_client.py | 42fb1d62d7a65177b0ed4ecfe963a04a7c445435b820b25416dd7a48cb47649b |
| app/experiments/minimal_procedure_transfer/run.py | b19f54af6833dbbd85a432fd2545ee7700ce1745ce7d47d60d9a7e3c2e56d447 |
| app/experiments/minimal_procedure_transfer/sandbox.py | a71ca55b41ac7d36f4a25813e69997516c3daf2bdfa02f39bcd8472b8bd705c2 |
| app/experiments/minimal_procedure_transfer/tasks.py | ae24f0d38c59697fe6583f53c4313dc4c12b5d3e26b1afee7ea449c77fd688f5 |
| app/experiments/minimal_procedure_transfer/tasks_v2_scratch.py | e25b3398f3d2f03d48c7de7193e8e1db83067331b6f45ef440c366af304cc8f6 |
| app/experiments/validated_experience_competence_transfer/CONTRACT.md | 60093559e923aa0bda478154fb770bba453d5ae28bfa1a0a2f5969288eaa6650 |
| app/experiments/validated_experience_competence_transfer/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/experiments/validated_experience_competence_transfer/consumption_signatures.py | da74be115ff448fe9d71162c66720d312a3a52123e112ca498c56cc52bdb6516 |
| app/experiments/validated_experience_competence_transfer/freeze_generic_tip.py | a3a5508d16b4cdaaa078dfd11a7c8a5851da8330e836881ba4476295c8446e40 |
| app/experiments/validated_experience_competence_transfer/freeze_procedure.py | 165b13e3d77ffe468880cd01e9db6ac226840a2235f47929316b0a6076e89f5c |
| app/experiments/validated_experience_competence_transfer/prompt.py | 90b6e7d550a680540eed89e3bfccabf23becd376ae3f3d807f4aabe55a3ed42f |
| app/experiments/validated_experience_competence_transfer/run.py | 59d8dfbe8b4ca4c022d6c85f71cf0aa3499d89d5a01be4fd353ba8099fc84e03 |
| audits/2026-09-23_historical_difficulty_headroom_calibration.md | c6a030bb17333b9e1c9a2a4c0bac58da9b4826946dedac6be2459895bf78c1b7 |
| audits/2026-09-23_validated_experience_competence_transfer.md | 5e27e1a2029b6fa426421a8ac456bdb0623436fe5f5a5961927a939107e86d03 |
| memory/experiments/validated_experience_competence_transfer/experience_log.jsonl | d63d60a611011a210d3bc057947c03dac8929d36e57c5dbdd3395d4c57e3daa5 |
| memory/experiments/validated_experience_competence_transfer/generic_tip_treatment.json | 8f1785d35d11a7a50e1c6adec714f250c83ed7c578a83c8715094ef2f315b90e |
| memory/experiments/validated_experience_competence_transfer/heldout_commitment.sha256 | f4f4f23df8160cd94d3f77ec25fbe6fec6ac2cc5982c4d26b6bb8ec15c72a9c8 |
| memory/experiments/validated_experience_competence_transfer/heldout_results.jsonl | 1bf688fd75bf1c779d5307cb597a816ccd7950bf86c1a1eb416365ce8370ac92 |
| memory/experiments/validated_experience_competence_transfer/heldout_tasks.json | 375884a58973a261ff20be308f33a6eaa9344be767b76a08b96167f11735e2fe |
| memory/experiments/validated_experience_competence_transfer/procedure_frozen.json | 3a466f4f4fdb1d77674e0875714bc13a35848dd8b0048cfc39a13d31c70b90f8 |
| memory/experiments/validated_experience_competence_transfer/procedure_hash.txt | 62a7ca9c80ffac60e827884296f632f10ff42289f47d85dbe4641c48490ebc3f |
| memory/experiments/validated_experience_competence_transfer/train_tasks.json | d510d4aa3467d0703b6d1548bc2e760e1dc1e63609d0008d19aa67eed11ba761 |

</details>

## 3. Attempted falsification of critique #1: acquisition provenance

### The strongest evidence against my original attribution

**OBSERVED.** Echo's local worker did materially generate ingredients of the later lesson before P was frozen:

| TRAIN episode | Machine-generated evidence preceding P |
|---|---|
| 00 and 06 | Successful line iteration, whitespace-stripped start checks including decorator/import/def/class, and return of the remaining suffix |
| 01 | Successful inclusion of a triple-quoted docstring start, line anchoring and suffix return |
| 02 | A regex already containing all seven later marker alternatives: from, import, def, class, @ and both triple-quote forms; it nevertheless truncated the code |
| 03 and 07 | Successful line-based extraction and suffix return |
| 04 | Failure caused by an unanchored keyword search matching prose |
| 05 | Failure caused by restricting starts to def/class and dropping the docstring |

These are preserved source outputs and grade records, not model self-reports. P is consistent with identifiable experience. It is too strong to imply that the local model contributed nothing substantive and Claude supplied an entirely unrelated solution. The later successful executable algorithm was also generated by the local worker, not pasted as finished candidate source by Claude.

### Exact actor/transformation chain

1. **Investigator-written generator:** constructs tasks from fixed prose/code banks and supplies task descriptions.
2. **Local qwen2.5-coder:7b request:** produces a candidate for each TRAIN task.
3. **Independent deterministic executor:** runs the candidate and records exact output versus construction-time expected output.
4. **Fixed retry wrapper:** appends the failed candidate and actual expected/actual feedback. All three retries fail, reproducing the initial candidate bytes.
5. **Investigator:** reads/interprets experience and writes the substantive three-clause lesson and episode-attribution dictionary into freeze_procedure.py.
6. **Freeze script:** reads experience_log.jsonl, checks that each cited episode ID exists, then serializes the already-written lesson and provenance dictionary.
7. **Later harness:** reads the frozen JSON, verifies its hash and inserts the lesson into the P prompt.
8. **Local worker:** generates the new executable extraction functions.

The attribution to Claude M5 as the investigator comes from the contemporaneous report. The code independently establishes the consequential distinction: **the lesson is external authored content, not output from an Echo lesson-extraction call**. Source alone is not cryptographic identification of which person/model typed that content.

### The decisive source check

I parsed V2 as syntax, without executing it. The stored context equals a leading newline plus its literal PROCEDURE_TEXT. The stored provenance dictionary equals its literal PROVENANCE.

The script's substantive verification checks episode-ID existence. It does not derive clauses from candidates, test whether the cited failure occurred, select a successful procedure, or call a learner. **Changing episode contents while retaining their IDs would not change the written lesson under this source.** This is a static counterfactual, not an intervention I ran.

The declared contract itself specifies extraction by “this investigator directly summarizing” the observations. Claude was therefore not merely launching a demonstrated existing Echo induction mechanism in this experiment.

Furthermore, the task description already names decorators, docstrings, imports and misleading prose words. The lesson could be constructed from the task schema and ordinary programming knowledge. Matching clauses to real experience does not establish that the experience was necessary to produce those clauses.

### Verdict on critique #1

**The central attribution survives; its strongest dismissive interpretation does not.**

- Machine-generated experience and reusable precursor behavior: established in the artifacts.
- External distillation of P: established by source structure, with the author identified by the report.
- Echo-autonomous extraction of P: **not demonstrated**.
- An external teacher's actual mental dependence on those episodes, rather than its task knowledge: supported by detailed correspondence, not identified by an experience-substitution comparison.
- “Experience-grounded, externally assisted teaching”: a reasonable bounded description.
- “Echo itself distilled this lesson from its own errors”: not supported.

An external artifact can be learned system state. What is missing here is identification of the acquisition mechanism and its experience dependence, not a model-weight update.

## 4. Attempted falsification of critique #2: novelty

I compared full task strings, exact expected-program bytes, their syntax-bearing content, prefix lines, ordered prefix layouts, and code-category/layout/separator combinations. Both corpora are the already-executed VECT corpora.

### Direct overlap findings

| Novelty level | Finding |
|---|---|
| New complete text | All 10 evaluation strings differ from all 8 TRAIN strings |
| New ordered prose combination | All 10 evaluation prefix sequences differ from TRAIN |
| New individual prose content | One evaluation case includes one prose-bank line absent from TRAIN |
| New instance | All 10 seeds are distinct from TRAIN; no full-input duplicates |
| New input arrangement | Five previously unseen P/D layout types occur in six evaluation cases |
| New category/layout/separator combination | All 10 such evaluation tuples are absent from TRAIN |
| New separator magnitude | None: both phases use counts 1, 2 and 3 |
| New underlying code content | None: every evaluation expected program exactly matches a TRAIN program |
| New program structure or opening category | None |
| New task family | None |
| New demonstrated failure mechanism | None beyond the already represented anchoring, start-marker and span-completeness issues |

P/D above means ordinary-prose versus distractor-prose line, not treatment arm. The five new layouts are DDPD, DDPP, DPDD, PDDDP and PDDPD. They are modest input-structure novelty, not new algorithmic task families.

The four shared exact snippets are:

| Code opening/content | TRAIN count | Evaluation count |
|---|---:|---:|
| import math / circle_area | 2 | 1 |
| @staticmethod / double | 2 | 3 |
| triple-quoted Utility function docstring / triple | 3 | 4 |
| from functools / lru_cache / fib | 1 | 2 |

There are four distinct expected-program strings in TRAIN, four in evaluation, and zero evaluation programs outside TRAIN. Since these are exact matches, merely normalizing names or comparing ASTs cannot reveal additional held-out program structure.

### What I previously undervalued

The objective is to locate a code boundary within prose, not to learn the behavior of fib or invent new program bodies. Reordering distractors, changing boundary separation and recombining those with opening categories produces legitimate new extraction instances. A requirement that every evaluation body be a new program would be stronger than the narrow task necessarily requires.

Nevertheless, this fixed four-program bank admits a simple answer-bank recognizer, and the same opening categories are taught and tested. It cannot establish transfer to new content, unrelated structures or task families.

The preserved P candidates actually use a general boundary rule rather than an answer bank. That source observation strengthens the interpretation of these modestly novel instances. It does not turn their reused contents into hidden new programs.

### Verdict on critique #2

**The four-snippet overlap finding survives exactly. An implication that there was no meaningful novelty is revised.** There is new-instance and limited compositional transfer, with no observed held-out program-content transfer.

## 5. Attempted falsification of critique #3: generalization versus instance fitting

### What the test actually ran

V3 lines 29–32 explicitly place the real grading input in the generation prompt. V1 lines 199–201 construct a one-element test list using that same input. All 30 held-out calls follow this design.

The earlier prompt language promising testing on “DIFFERENT input strings” does not establish such testing. The actual caller determines what was tested.

I found no later VECT artifact containing independent hidden inputs, a frozen-candidate cross-case test matrix, or a second validation run. The older minimal-transfer executor can accept multiple tests, but that capability was not used for VECT.

### Strong counterevidence in the preserved candidates

Exact SHA-256 grouping of P extracted source gives:

| Candidate-source SHA-256 | Evaluation cases | Recorded successes | Code categories |
|---|---|---:|---|
| 870427457e4b8a13511a2f3340c8737cdf34e2df4a3132d2cfffd96d27e99d44 | 00, 08, 09 | 3/3 | Decorator |
| 837d272f31e466daa7d292f5704c29f36601d970b1ea0f412780cb16652f1ba2 | 01, 02, 03, 04, 06, 07 | 6/6 | From-import/decorator, docstring, import |
| f090d2a3ab8d6ea111f134e164c5748abcb6ffb533149943ce0462f7d91fb631 | 05 | 1/1 | From-import/decorator |

These hashes identify code, not merely similarly worded prompts. The first six-case program had already appeared for case 01; identical bytes subsequently worked on five different strings.

**This is existing multi-input evidence for the same program text.** It is not a prospectively locked candidate tested against concealed inputs: each later call again saw its own input, and the analysis grouping candidates by equality is retrospective. But treating these observations as only ten unrelated per-instance solutions would throw away real evidence.

All three source variants implement equivalent logic:

1. Split the runtime argument into lines.
2. Find the first line whose whitespace-stripped form starts with one of the seven markers.
3. Return the original lines from that position to the end.

They contain no expected-answer literal, task-ID routing, snippet table, file reads or external calls.

### Static generality argument

For any string whose preceding prose lines do not start with these markers after stripping, whose first code line does, and whose correct output is the complete remaining suffix, this algorithm returns that suffix without depending on its particular content. New variable names, function bodies and lengths do not affect that argument.

This is a conditional source-level deduction, not newly generated data or an empirical estimate on additional tasks. It fails outside its assumptions—for example, prose beginning with a marker or trailing commentary. Level 3's generator makes those assumptions favorable.

### Verdict on critique #3

**The design criticism survives; my strongest interpretation is corrected.**

The experiment did not demonstrate prospectively concealed-input validation. It did preserve genuinely reusable implementations, including repeated exact-source success across different inputs. Calling the result mere instance-specific fitting is unsupported for these P outputs.

## 6. Statistical reassessment and result integrity

### Recomputed ledger

There are 8 TRAIN episodes: 5 first-attempt passes and 3 first-attempt failures. Exactly those 3 receive retries; all 3 retries fail and reproduce their first candidate source exactly. Total TRAIN calls: **11**.

There are **30** held-out records: exactly one for every pair of 10 task IDs and 3 arms, in P/G/Z order. No duplicate pair, missing pair, logged retry, exclusion, or nonempty client-error field was found. TRAIN seeds are 1000–1007; held-out seeds are 1100–1109.

I independently compared every available per-test input and expected string to its task record and recomputed equality from the recorded actual output. Every passing result has exactly one successful comparison. There are 21 passed/graded records, 7 wrong-output records and 2 runtime-error records.

| Case | P | G | Z |
|---|---:|---:|---:|
| 00 | 1 | 1 | 1 |
| 01 | 1 | 1 | 0 |
| 02 | 1 | 0 | 0 |
| 03 | 1 | 0 | 1 |
| 04 | 1 | 0 | 0 |
| 05 | 1 | 1 | 0 |
| 06 | 1 | 1 | 1 |
| 07 | 1 | 0 | 0 |
| 08 | 1 | 1 | 1 |
| 09 | 1 | 1 | 1 |
| **Total** | **10/10** | **6/10** | **5/10** |

This is read-only regrading of saved outcomes, not new candidate execution.

### Prespecified paired analysis

The same tasks receive every treatment, so matched discordant-pair analysis is appropriate for the stated panel. An unpaired test would discard that structure.

| Comparison | Wins / losses among discordant pairs | Observed difference | Exact one-sided p | Exact two-sided p |
|---|---:|---:|---:|---:|
| P–G | 4 / 0 | +40 percentage points | 0.0625 | 0.125 |
| P–Z | 5 / 0 | +50 percentage points | 0.03125 | 0.0625 |
| G–Z, descriptive | 2 / 1 | +10 percentage points | 0.5 | 1.0 |

These follow directly from binomial tail probabilities with discordance probability one-half. I did not search alternative tests for a favorable threshold. The contract calls for paired exact McNemar, two-sided reporting and separately stated one-sided interpretation.

Nominal marginal 95% Wilson intervals reproduce:

| Arm | Accuracy | Wilson interval |
|---|---:|---:|
| P | 1.00 | 0.7225–1.0000 |
| G | 0.60 | 0.3127–0.8318 |
| Z | 0.50 | 0.2366–0.7634 |

These are the requested binomial summaries, not cluster-adjusted intervals or intervals for the paired treatment differences.

### What the small panel can and cannot support

- The positive point estimates are substantial. A p-value above .05 does not show absence of benefit.
- Conversely, one unadjusted one-sided P–Z p-value below .05 cannot establish the full provenance/retention/transfer claim. It does not resolve P–G, multiple comparisons or acquisition provenance.
- G and Z have not been shown equivalent. “G ≈ Z” is a descriptive impression, not an equivalence result.
- The ten input strings are the paired evaluation units for this run, but share four code templates and one lesson-extraction history. They are not ten independent acquisitions or ten families.
- The fixed P/G/Z ordering is confounded with treatment. Fresh requests remove conversational history sharing; they do not prove a time/backend/order effect impossible.
- Requested temperature, seed, token ceiling and context ceiling are identical. Actual token usage was not retained, so equal ceilings should not be described as verified equal inference cost.

The concentration of the advantage is particularly revealing:

| Snippet stratum | Cases | P | G | Z |
|---|---:|---:|---:|---:|
| Decorator | 3 | 3 | 3 | 3 |
| Import math | 1 | 1 | 1 | 1 |
| Docstring | 4 | 4 | 0 | 1 |
| From-import/decorator | 2 | 2 | 2 | 0 |

**Every P–G gain occurs on the same docstring-bearing underlying snippet.** That is a useful improvement across its varying surroundings, but not four independently replicated discoveries. This is descriptive subgroup analysis, not a newly selected hypothesis test.

### Parsing and evaluator caveats that do not change these counts

The two Z runtime errors, cases 01 and 05, are not evidence of length-terminated generation. Their complete raw responses contain a regex for fenced Python text. The executor's fence extractor stops at literal triple backticks inside that regex, leaving an unterminated string in the extracted candidate.

Thus the measured pipeline includes an output-parsing failure. However, source inspection shows the intact raw function searches the input for a fenced code block; these task inputs contain none. Even without the parsing problem, that particular algorithm would not solve these cases. I neither repaired nor executed it, and retained both failures in the denominator.

The client returns model identity and done_reason, but VECT's logger omits both. Requested qwen2.5-coder:7b and sampling parameters are recoverable from source; exact served weight digest and per-call finish reason are not. Raw output exists for every held-out record. There is no basis for labeling these two errors as empty or budget-terminated responses.

V6 is an execution-based exact-match checker, distinct from production F2. It passes inputs, not expected values, to its subprocess. However, its parent comparison zips tests and returned results without checking their lengths: an empty result list could yield a vacuous pass under the source. **No observed success uses that path**: all 21 saved successes contain one actual equal result. The P functions also contain no grader-interaction code. This latent weakness limits general evaluator qualification; it does not erase the recorded successful equalities.

### Verdict on the statistical criticism

**The original numerical characterization was fair and reproduces.** It would be unfair to turn it into “there is no observed advantage.” The result is a promising small-panel treatment effect, not a statistically secure population claim or proof of autonomous learning.

## 7. Previously overlooked evidence and attempted triangulation

I searched outside VECT specifically for a stronger existing experience → state → boundary → retrieval → behavior → ablation chain. The following are separate experiments, not extra samples to pool with VECT.

### 7.1 Real automated experience extraction already exists

H3's lesson_mining.py extracts historical NameError identifiers, counts and failure/retry-success associations from watchdog logs. This corrects any repository-wide claim that no machine-driven experience-to-state transformation exists.

But its general lesson about importing or defining missing names is a fixed authored sentence template. The log matcher does not inspect historical corrected candidate source to establish that every successful retry actually implemented that particular repair. Its verified flag means a matched failure/retry-success signal, not semantic proof of each correction.

The preserved clean-transfer pair contains different control/experience prompts but **byte-identical generated code**, SHA-256 6496fa4e19101a1e6a339f4972cf8c4fce8b3bdc486b67f4dba40a1008fdb3dc. The older four-row series records control passes on both tasks, experience passing one and failing one. Neither supplies a replicated correctness advantage. Later pipeline-collapse diagnostics further caution against treating a single identical-output pair as a universal learning impossibility.

This machinery is not called by VECT's procedure writer. Its existence therefore does not transfer automated-extraction provenance to P.

### 7.2 Architecture A: a relevant actual null result

H4 contains 12 trial records: 6 control and 6 experience, with **5/6 retry successes in each condition**. A failure-derived diagnostic was injected. There is no observed advantage in that panel.

The success criterion there is the production self-edit sandbox/importability path, not VECT's exact task-output correctness. It cannot be added to VECT's successes as independent confirmation of task learning. It remains useful negative evidence about one intervention, not proof that experience-based improvement is impossible.

### 7.3 Durable directives can influence later fresh-process behavior

H5's raw results contain:

- baseline marker compliance: 0/2;
- immediate exposure after writing a confirmed directive: 2/2;
- later restart/paraphrase phase: 1/2;
- unrelated controls: 0/2;
- near-miss trigger: 0/1.

The source provides separate phase entry points, disk state loading and direct context construction. The directive is human-confirmed, explicitly authored instruction. The later phase is reported as a separate subprocess; the raw records alone do not carry process IDs. The harness invokes structural-ground-truth context construction directly rather than establishing every ordinary production routing path.

Cleanup records successful deletion, **but there is no post-deletion behavioral retest in this ledger**. It is inaccurate to transform deletion into demonstrated loss of improvement.

This is evidence that an external durable behavioral artifact can be recovered and sometimes affect fresh-context behavior. It does not identify autonomous lesson formation or independent task-competence improvement. It is also not the same artifact or mechanism as VECT P.

### 7.4 The earlier micro-world retention pilot does not supply missing positive transfer

H6 preserves 24 records: two models, four conditions, three test categories, one world. For echo:latest, the recorded scores are:

| Condition | Correct | Incorrect | Ambiguous |
|---|---:|---:|---:|
| Rule directly in context | 3 | 0 | 0 |
| Session boundary without rule context | 1 | 2 | 0 |
| Persistent-memory retrieval | 1 | 1 | 1 |
| Retrieval blocked | 0 | 2 | 1 |

Persistent retrieval records actually contain the formation information. This is stronger evidence of experience availability than an empty memory claim. But its novel-category response is incorrect; it does not demonstrate reliable retained transfer.

Some responses use initial letters instead of the expected answer format, so parser labels should not be confused with pure competence measurements. The source also explicitly teaches the invented world's rule; it is not an autonomous rule-induction test. These limitations prevent treating this pilot as decisive negative evidence as well as positive evidence.

### 7.5 Other saved data constrain overgeneralization

- H2's merge-interval baseline passes **5/5** without a learned procedure. No procedure artifact or completed transfer phase exists there. This demonstrates useful model-native competence and explains why that branch could not establish incremental acquisition.
- H1's corrected qwen calibration records 5/5 at Level 1, 5/5 at Level 2, 5/10 at Level 3 and 0/5 at Level 4. VECT follows deliberate headroom selection; its ten-case panel is not an unbiased estimate across arbitrary programming tasks.
- H7's July memory-ablation file contains 30 paired responses and five noise-floor pairs, measured using response distances and heuristic quality scores rather than independently verified new-task correctness. The September nonpersonal file contains only one pair, zero noise-floor pairs and zero quality-score difference. These files do not establish the missing competence-transfer chain.
- Searches for the actual VECT state path and held-out IDs found the known driver, report and later prose references, not a later independent VECT validation corpus.

**Conclusion:** the repository contains real persistence, retrieval, automatic historical extraction and context-conditioned behavior. These strengthen the feasibility of system-level learning. They do not jointly identify a causal chain that no individual experiment demonstrates. I found no separate positive experiment that removes P's external-teacher explanation.

## 8. Strongest non-learning / external-assistance doppelgänger

Consider this system:

1. Use a fixed pretrained local code model.
2. Generate the same TRAIN candidates and log their real outcomes.
3. Have an external expert write the complete-marker, line-start, take-to-end lesson using the public task description and ordinary programming knowledge. The expert may inspect the logs and cite examples, but the lesson does not require an Echo-operated learner.
4. Save the fixed lesson as JSON and hash it.
5. For each new task, start a fresh model request, load the JSON and append it to the prompt.
6. Let the fixed model compile the instruction into the general extraction function.
7. Compare against untaught and generic-guidance prompts.

**This reproduces every surviving VECT observation**, including meaningful compositional cases, repeated identical general programs, durable storage/recovery, static consumption signatures, the P/G/Z accuracy pattern and the disappearance of P's advantage when its guidance is absent.

It does not require an answer lookup table or hardcoded outputs. A general, useful procedure can be elicited by an external task expert without the evaluated system having acquired that procedure from its own experience.

The doppelgänger need not reproduce the exact random output of every request with mathematical certainty. It is an observationally compatible causal account using precisely the mechanism present in the source; no special hidden privilege is needed.

Calling it “non-learning” is scope-dependent:

- The frozen worker alone need not learn anything persistently.
- The externally edited model-plus-file workflow changes retained instruction and can become more useful.
- If Claude is included inside a broader teacher–student system, one may reasonably call this externally assisted learning.
- That broader boundary cannot silently become evidence that Echo's own acquisition machinery extracted the lesson.

The unobserved discriminator is what an independently fixed Echo learner would retain under different evaluated experience, with external task-specific lesson writing removed.

## 9. Causal-chain grading

The target of these ratings is the user's full question about Echo acquiring retained competence from its own experience. Notes distinguish the narrower assisted chain.

| Link | Rating | Evidence and boundary |
|---|---|---|
| EXPERIENCE | **ESTABLISHED** | Eight actual recorded task episodes; 11 candidate calls; exact outputs and three failed retries. This is local-worker experience in a standalone FeralEcho research harness. |
| LESSON EXTRACTION | **NOT DEMONSTRATED** | Echo-autonomous cross-episode extraction is absent from the source. External extraction is supported by clause/episode correspondence, and its authored literal is preserved. The counterfactual dependence of that external lesson on the experience is untested. |
| RETAINED CHANGE | **ESTABLISHED** | A specific procedural context is durably stored, with a matching canonical hash. This is retained external instruction, not demonstrated changed weights or production policy. |
| BOUNDARY | **ESTABLISHED** | A fresh single-turn model-context boundary is explicit in the client; TRAIN history is not included except via the assigned lesson. This rating does not assert an independently attested full Echo/Ollama process restart. |
| RECOVERY | **ESTABLISHED** | Held-out source loads the JSON from disk, verifies its hash and inserts its text. Preserved P source behavior is consistent with that consumption. No broader autonomous-memory retrieval is implied. |
| NOVEL APPLICATION | **SUPPORTED BUT LIMITED** | New text/combinations/layouts, plus repeated same-source success and a conditional generality argument; no new program content or prospectively concealed-input test. |
| MEASURABLE ADVANTAGE | **SUPPORTED BUT LIMITED** | 10/10 versus 6/10 and 5/10 on the paired panel. Small sample, four shared templates, fixed treatment order, one extraction history and incomplete cost/model provenance limit inference. |

The missing extraction link cannot be filled by the established storage and consumption links. Conversely, the missing extraction link does not invalidate the useful behavior actually observed downstream.

## 10. Strongest justified claim

**In a standalone FeralEcho research harness, loading a frozen, externally distilled lesson into fresh local-model contexts produced reusable extraction code and higher observed exact-match accuracy on ten newly combined task inputs—10/10 versus 6/10 with generic guidance and 5/10 without guidance. This supports persistent, externally assisted procedural guidance and limited compositional application; it does not yet identify Echo's autonomous acquisition of the lesson from its own experience.**

A shorter answer to “Can Echo become better because of experience, retain the change and use it on new cases?” is: **the retained-guidance and new-combination parts have stronger evidence than I previously credited; the attribution to Echo's own experience-driven acquisition remains unproved.**

### Capability provenance, kept separate

| Category | What these artifacts support |
|---|---|
| Foundation-model-native capability | Strong precursor behaviors already appear without P; code synthesis occurs in the fixed local model |
| Echo architectural/scaffolding capability | This standalone experiment stores, hashes, reloads, prompts and grades; it bypasses live Echo's normal learning/routing machinery |
| Within-context adaptation | The model responds to the lesson supplied in its current request |
| Echo-autonomously acquired competence | Not demonstrated by P's production path |
| Externally assisted acquired competence | Supported in the bounded teacher-plus-retained-guidance sense, with causal provenance limitations |
| Persistent external memory/instruction | Directly established |
| Unknown-origin capability | Exact pretrained origin of the worker's algorithmic knowledge and exact served model digest remain unknown |

## 11. Explicitly unjustified claims

The current evidence does not justify saying:

- Echo independently discovered or distilled P from its own evaluated errors.
- Claude was merely operating an existing Echo extraction mechanism in this run.
- The ten evaluation programs were unseen during TRAIN.
- Every success was only an instance-specific hardcoded answer. The source contradicts that dismissal.
- A frozen candidate was prospectively evaluated on concealed additional inputs.
- A complete production Echo restart and autonomous retrieval were demonstrated by VECT.
- P improved arbitrary code extraction, Level 4 trailing-commentary handling, new program structures or other families.
- P–G cleared the conventional one-sided .05 threshold, or G and Z were established equivalent.
- The marker signature proves causal necessity of each lesson clause. No clause ablation was performed, and the signatures are static.
- A hash proves investigator blindness or a fixed model digest.
- Separate persistence, memory-ablation and retry experiments can be pooled into a single proven acquisition chain.
- This establishes repeated accumulation, learning-to-learn, open-ended competence growth or foundation-model learning.

The opposite universal claim—“Echo cannot learn because its model weights are frozen”—is also unjustified.

## 12. Single highest-information next experiment

**A prospectively frozen, Echo-only acquisition experiment with counterfactual experience and retained-state crossover. Do not run it under this report's authority.**

Use matched, newly drawn task worlds whose useful rule differs in a prospectively protected way. Freeze the learner and its update/extraction procedure before exposure. Echo alone receives evaluated experience and writes the retained state; an external investigator may execute the protocol but may not supply or edit the substantive lesson.

After a clean process boundary, test each independently acquired state on fresh cases from its matching world and on a matched alternative world. Include removal and cross-world substitution of the retained state, while holding the generation/evaluation conditions fixed. A task-description-only competent baseline must receive the same legitimate task information and budget. Generate or freeze the candidate before revealing the additional evaluation inputs.

The decisive pattern is not merely “state present beats state absent.” It is that:

- changing only acquisition experience predictably changes what Echo retains;
- matching retained state improves genuinely unseen-case correctness;
- removing or swapping that state removes or redirects the advantage as predicted;
- an externally unassisted, fixed learner reproduces that chain across independent histories.

This single crossed design targets the present ambiguity: experience-caused acquisition versus externally authored, model-native task guidance. It can use explicit rules or lookup/statistical state; it need not demand weight changes or new-procedure acquisition. Replication should be sized from a prespecified meaningful effect and history-level variability, not selected afterward for significance.

**No implementation, new candidate execution, learning experiment or evidence repair was performed.** The only file created by this review is audits/2026-09-24_codex_validated_experience_transfer_self_falsification.md. Previous reports and evidence were preserved.

**Final integrity check:** At 2026-09-25T05:02:41.504911+00:00, all 32 fingerprinted source/evidence files still matched their opening byte hashes, HEAD was unchanged, and the complete working-tree comparison showed exactly one addition: this report. No pre-existing status entry was removed or changed. The pre-existing 28 tracked modifications remain; the untracked-file count is now 350. This final integrity statement is the only subsequent edit, within the newly created report itself.

ORIGINAL CRITIQUE: PARTLY REVISED
