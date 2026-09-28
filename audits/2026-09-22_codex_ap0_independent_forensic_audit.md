# AP-0 independent forensic and adversarial audit — 2026-09-22

**Author:** Codex. **Scope:** AP-0 / accumulation_probe. **Mode:** read-only investigation; this report is the sole authorized write. **Stage 1 was not run.**

## 1. Executive verdict

**AP-0 establishes that a frozen local coding model can use supplied, task-relevant conventions, and that it can transcribe K1 examples into useful procedure text. It does not establish accumulated competence, autonomous learning, foundation-model learning, or a qualified general acquisition pipeline.**

The primary Stage 0 effect is real within this apparatus: H passes 44/54 primary calls versus 0/54 for each of N, NEUTRAL and MISMATCH. I independently reproduced all 554 Stage 0 binary grades. That establishes instruction consumption and content sensitivity. It is not an acquisition experiment.

Qualification separates several problems that must not be called one “learning failure”:

- K1: the raw drafts contain correct known-code tables; a frozen regex auditor falsely rejected them. Corrective reanalysis is justified, although still post hoc.
- K2: constructors repeatedly restate the ranking schema without extracting its identifiable priority order. Separately, the worker sometimes reverses an explicitly correct order. Both construction and execution fail.
- K3: the prompt never supplies the restricted operation family used by the evaluator and later symbolic diagnostic. Many generated rules also contradict observed examples. QB adds a major generation confound: five of six K3 responses are empty and length-terminated.

**The pooled qualification gate fails its own frozen requirement:** GOLD acceptance is 10/12 = 83.33%, below 85%. Under the actual rule, K1 is PARTIALLY QUALIFIED, K2/K3 NOT QUALIFIED, and no convention is fully QUALIFIED. A claim that only K2/K3 block the current qualification is incomplete.

**A non-learning doppelgänger survives.** A fixed example-to-instruction compiler, followed by ordinary file storage and the frozen worker, can satisfy the intended behavioral pattern. Its output can depend on experience without its hypothesis language, execution capability, or learning mechanism improving. The proposed controls do not distinguish that explanation from stronger acquisition language.

**A separate adversarial defect is confirmed:** candidate code and hidden answers share a Python module. A function that simply reads the global answer table passes all 52 stored Stage 0/qualification test modules in an in-memory reproduction. No examined historical output uses this shortcut, and historical grades independently reproduce without it. Thus the data are usable with caveats, but claims of an adversarially isolated grader are false.

Stage 1 is **NOT READY**. This is a falsifiable proposal for a narrow artifact-construction effect once specified and qualified; it is not a test that can reject fixed compilation as an explanation of success.

## 2. Git and evidence integrity before/after

Integrity measurements and final status comparison are recorded in §21 and Appendix B. Initial HEAD was **2fba42644c82b9f7096276f4dd338d615cf1bcce**, branch main, 17 commits ahead of origin/main. Initial porcelain-v2 status contained **27 modified tracked paths, no staged changes, and 262 untracked paths**. The AP-0 package and protocols were already untracked. A path-limited Git log across all refs returned no AP-0 history. Consequently the substantive experiment timeline rests on local freeze records, ledgers and file metadata, not committed AP-0 revisions.

Before analysis, I fingerprinted **162 pre-existing files, 24,477,086 bytes**, covering the complete existing AP-0 artifact tree and package, relevant protocols/verifiers, all initially modified tracked files, Git index/HEAD/main ref, and selected production-state sentinels including FAISS and memory metadata. Hashing an existing review file for integrity did not involve reading its interpretation. The baseline was held in audit-session memory; no snapshot file was created.

| Boundary | Independently verified coverage | Limitation |
|---|---|---|
| Stage 0 FREEZE | 32 artifact hashes, 14 source hashes, protocol, sidecar, sandbox profile/wrapper; all match | Local self-recorded timestamps; no independent timestamp authority; new files are not covered merely by being in the directory |
| QUAL FREEZE | Four artifacts, 23 source files, protocol; all match | Gate inputs, results, corrective auditor, QB and later solver were not in this original set |
| GATE_INPUTS | Request-file hash and QUAL-freeze link | A later local commitment, not the original constructor freeze |
| QB FREEZE | QB request file, QB source, corrective auditor, QUAL-freeze link | Separate pre-QB amendment, not proof the original QUAL protocol prescribed every QB detail |
| Ledgers | 1,094 response rows; hashes, chains, request and seed derivations match | Local hash chains are not signatures; wholesale rewriting and recomputation is not cryptographically excluded |
| Development | 192 rows and response text, plus worlds/task metadata | No equivalent freeze, full request bodies, model digest per row, response-hash chain, or saved hidden-case file |

Freeze SHA-256 values:

~~~
Stage 0: 43aca7d451a259299a2e128521130bd6b861f51275990878c42e22ef3e1c0522
QUAL:    cf184d8616f33693dc75b344a382f6ea5458e2ee929204c5a598b8f352b40e7d
QB:      493d8693b03c59c95fbab25ef7fcdfe89fdefce7f9ad56c0246f9cfd99d14d77
~~~

Recorded worker/QA identity is qwen2.5-coder:7b, digest dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364. QB is deepseek-r1:7b, digest 755ced02ce7befdb13b7ca74e1e4d08cddba4986afdb63a480f2c93d3140383f. Both snapshots report Ollama 0.34.2. These are verified records, **not a live attestation of loaded weights during every call**. I made no server/model API requests.

The initial Stage 0 driver checks model identity and logs an unchanged digest at completion. QUAL generation does not enforce an equivalent per-call/end check; its direct “construct” path does not call verify_freeze first. QA verification does not rehash its protocol or self-anchor FREEZE_QUAL; the current files nonetheless match their recorded hashes. QB generation similarly relies on a previously written freeze. These are enforcement gaps, not evidence that the recorded experiment was altered.

## 3. Independent AP-0 reconstruction

The research question has three distinct levels:

1. **Stage 0:** can this worker use this carrier?
2. **Proposed Stage 1:** can episode-derived, independently accepted text persist and cause correct performance on held-out inputs?
3. **Future accumulation:** does acquiring additional state accumulate competence? No such test is present.

The concrete apparatus is an isolated research harness that calls local Ollama directly. It does not run the production FeralEcho deliberation, RiverBrain, FAISS, memory-learning, or self-edit path. Its principal knowledge carrier is text in the system prompt, labeled retained notes. H's “earlier experience” label is a standardized prompt wrapper around hand-written oracle knowledge, not evidence that H learned anything.

### Families and task coverage

| Family | World generator | Stage 0 T | Stage 0 S | v2 additions |
|---|---|---|---|---|
| K1 | Six invented codes; two each assigned open/closed/hold | Totals, counts, category IDs, top category | Tuple records; semicolon log | Category-specific sum; sorted totals; status/amount pairs; merged batches |
| K2 | Four invented tags; fixed priority, with generator rejecting orders unless exactly two adjacent descents | Winner, full ranking, loser, top two | Dictionary entries; round winners | Winner/score; is-winner; text entries; per-round rankings |
| K3 | Four event tokens, one each add/subtract/multiply/set with constants | Final state, trace, maximum, first-over-limit | CSV events; batches resetting to start | Minimum; count-over; run-length events; named runs |
| NEAR | Explicit task convention conflicts with carrier | Two tasks per family in Stage 0 | — | Six per family in v2, several replaced rather than merely enlarged |
| UNREL | No site convention | Sum evens, reverse words, flatten, run-length encoding | — | Maximum, vowel count, unique sort, palindrome, second distinct maximum, chunking, inversion, FizzBuzz |

Stage 0: 12 T + six S + six NEAR + four UNREL = 28 tasks, ten hidden cases each. One true world and one foreign world per family. Stage 1 proposes two realizations, 30 T/S templates per world, 18 NEAR and 12 UNREL templates.

The generator's K3 bounds are add 2–9, subtract 1–5, multiply 2–4, set 3–9. The learner is not told those bounds or even that these are the only four operation kinds. K1's balancing constraint and K2's rejection-sampling constraint are likewise generator knowledge, not learner-visible requirements. Frozen Stage 0, development and qualification world JSON all reproduce from independently implemented seed logic and the current dictionary-screening file.

### Arms

N has no note. N2 repeats it with another seed set. NEUTRAL supplies a foreign convention of the same family. MISMATCH supplies the actual tokens with incorrect assignments/order/operations. H supplies the correct procedure; H2 repeats it with another seed set. E supplies raw examples inside retained notes; IC supplies those examples in the user message.

H/NEUTRAL/MISMATCH are character-length matched in Stage 0: K1 542, K2 582, K3 381 characters including carrier formatting. Character matching is not tokenizer-level matching. H's unrelated controls appear under three family notes; this creates 12 task/carrier units from only four unrelated tasks.

Stage 1 adds P, the first draft passing validation; P-X, the other world's retained note; and the first naturally failed draft. These are proposed arms, not collected Stage 1 data.

### Constructor and gate qualification

QA uses the worker model as constructor, with temperature 0.5, top_p 0.95, 400 predicted tokens, context 4096 and repeat penalty 1. R0 uses six K1, four K2, or eight K3 episodes. R1 uses 12 episodes per family: two amounts per K1 token, both name orders for every K2 tag pair, and three start states per K3 event.

**R1 is not just a representation manipulation:** it also adds evidence. Consequently R0/R1 cannot isolate formatting from information content.

Each family has two qualification worlds, three drafts per main representation, and two drafts per adversarial variant/world. A1 removes all evidence involving a token; A2 shuffles R0; A3 mixes R1 with four examples from another family. Total: 72 QA drafts. Twelve GOLD, twelve WRONG and twelve NONE gate trials supplement draft trials; each trial asks the worker to solve four validation templates, one sample per task.

The validation templates were selected prospectively for QA, after development, using Laplace-smoothed H success pooled across Stage 0 H/H2 and development. I independently recovered:

- K1: T1, T2, S1, S2.
- K2: T1, T6, S1, S3.
- K3: T4, T1, S1, S4.

The gate accepts at least two of four task programs. Three-of-four is descriptive. QA constructs all drafts before gate evaluation; it does not perform the proposed adaptive three-draft retention procedure.

QB is the single pre-named alternative model, on K2/K3, R0 only. Its token budget was raised to 3,000 in a separate pre-QB freeze; main drafts were attempted first, with adversarial variants conditional on clearing the exactness bar. No further constructor was used in this audit.

### Grader and deterministic helpers

Test construction generates a pool, selects cases to kill specified mutants, then pads to ten. A second implementation checks expected answers. The candidate is extracted from the last relevant code fence and concatenated with hidden test source; a random marker signals apparent success. This is stronger than matching answer prose but weaker than isolating an untrusted program from its evaluator.

Deterministic machinery supplies world creation, episode selection, schema, applicability text, H/MISMATCH/NEUTRAL notes, seeds, task templates, test generation, mutation operators, code extraction, regex content audits, gate thresholds, bootstrap analysis and all orchestration. The later symbolic diagnostic supplies an additional hand-designed hypothesis language. These components do substantive work.

## 4. Evidence timeline and classification

Times below are UTC. Ledger/freezes contain self-recorded times; file modification times are weaker supporting evidence, not immutable provenance.

| Time | Evidence/event | Classification |
|---|---|---|
| Sep 13 22:27:43 −07:00 | Current HEAD committed; AP-0 absent from Git history | Historical repository anchor |
| Sep 21 16:07–16:08 | Stage 0 worlds/plans/oracles and instrument records created | PRE-REGISTERED apparatus, covered by subsequent freeze |
| 16:09:17 | Stage 0 FREEZE | PRE-REGISTERED within the local record |
| 16:09:25–18:31:22 | 554 Stage 0 calls, interleaved shards, one completed pass | Frozen experiment |
| 18:34:08 | Primary scoring output | Execution of frozen analysis |
| 18:36:23 | NEAR/power/table-content addendum | POST-HOC, DIAGNOSTIC |
| 19:29:04; 19:31:22 | Re-audits, three surviving extra mutants; corrected interpretation | POST-HOC, CORRECTIVE/DIAGNOSTIC |
| 19:37–20:25 | v2 development, 192 calls | DIAGNOSTIC, not equivalently preregistered |
| 20:49; 20:50:34 | Dev-only validation selection, then pooled selection | CORRECTIVE to design; prospective for QA |
| 20:51:04; 20:53:04 | QUAL protocol and FREEZE_QUAL | PRE-REGISTERED for QA after development |
| 20:53:13–21:02:33 | 72 QA constructor responses | Frozen QA |
| 21:02:53 | 432 gate requests committed; generation starts | Prospective derived gate inputs |
| 21:07:38 | Corrected K1 auditor | POST-HOC, CORRECTIVE; after drafts, during gate collection |
| 21:08:32 | QB freeze, 3,000-token budget | PROSPECTIVE BUT NOT PRE-REGISTERED in original QUAL settings; contingency identity was preregistered |
| 21:08:52 | Hand adjudication record | POST-HOC, CORRECTIVE |
| 21:14:08 | Current Stage 1 draft mtime | PROSPECTIVE BUT NOT PRE-REGISTERED; still contains a results placeholder |
| 21:14:40 | Current v2 verification script mtime | Post-freeze test evolution; not itself in original QUAL code-hash map |
| 21:19:20–Sep 22 01:00:01 | 12 QB responses | Pre-QB settings recorded; overlaps ongoing QA gate |
| Sep 22 00:39:14 | Last QA gate response completes | End QA generation |
| 00:43:17; 00:43:56 | Original and corrected QA summaries | Frozen analysis, then disclosed corrective analysis |
| 11:54:18–11:55:40 | 24 QB gate responses | Qualification only |
| 11:55:49 | QB summary | Qualification analysis |
| 12:06:36; 12:08:17 | Current symbolic solver and verification source mtimes | POST-HOC, DIAGNOSTIC; neither is preregistered acquisition evidence |
| 12:14 onward | This audit, primary sources first | Independent read-only examination |
| 12:23:46 | Provisional conclusions recorded in this report | Pre-dedicated-review checkpoint, preserved in Appendix A |

The original QUAL contingency says “after phase QA”; actual QB generation began before QA's gate finished. Exactness failures already made K2/K3 ineligible, so the overlap does not by itself reverse a finding. It is nevertheless a protocol-sequencing deviation and prevents describing the entire process as strictly serial.

The Stage 1 draft is especially weak as evidence of completed qualification: it predates completion, includes “<<QUAL_RESULTS>>”, and says zero leaks were observed in 432+72 requests while the gate collection was still underway by file timestamps. That statement may reflect scans of planned requests, not a completed run. I independently scanned the completed requests later and found no hidden-case literal matches.

Other changes are not silently retroactive: the original files and original negative result under the broken K1 auditor remain available. That preservation is a strength. A current green verifier does not make its later additions part of an earlier freeze.

### All decision thresholds

Stage 0 frozen constants: H−N and H−NEUTRAL at least 0.30 with one-sided 95% bootstrap lower bounds at least 0.15; per-family H−N at least 0.30 in two of three families; N at most 0.40; absolute N/N2 and H/H2 rate differences at most 0.10; H−MISMATCH at least 0.20; regrade agreement at least 0.99; infrastructure failures at most 0.02; truncation at most 0.05; 10,000 bootstrap resamples. Original oracle disagreement/mutant/spoof counts must be zero and all planned calls completed. If headroom failed, IC−N ≥ 0.30 was a non-gating format-consumption diagnostic. The original provisional Stage 1 thresholds were +0.25 transfer, +0.30 headroom and a ±0.10 negative-control equivalence band; the later draft retains the gain/headroom magnitudes while changing the control criterion.

QUAL frozen constants: gate at least 2/4; two control seeds; exactness qualification at least 5/6; NOT QUALIFIED at most 1/6; adversarial unsafe acceptance at most 0.25; pooled GOLD acceptance at least 0.85; pooled WRONG/NONE acceptance at most 0.05; three main drafts, two adversarial drafts, two worlds. Before this freeze, development motivated changing the proposed gate from 3/4 to 2/4 and choosing pooled rather than dev-only templates.

Current Stage 1 draft: at most three drafts; gate 2/4; P−NEUTRAL at least 0.25 with lower bound at least 0.10; P−MISMATCH at least 0.25; own-world versus P-X at least 0.20; P−FAILED-DRAFT at least 0.20 when a failed draft exists; NEAR lower bound at least −0.15 relative to NEUTRAL; UNREL drop at most 0.10; H−NEUTRAL headroom at least 0.30 per convention; 10,000 bootstrap resamples. Integrity adds regrade at least 0.99, infrastructure at most 2%, truncation at most 5%, hash/request/model/boundary checks, zero forbidden sealed reads and zero spoof passes. These are prospective choices, not accomplished gates.

## 5. Recomputed numerical evidence

### Method and limits

I did not run repository verifiers or any model generation. For independent regrading, I parsed hidden case literals with AST, extracted recorded candidate functions, screened their ASTs for external effects, and executed them in a fresh audit interpreter with restricted builtins, controlled imports and a step bound. Cases were supplied outside the candidate namespace, with deep copies. One Stage 0 candidate calls eval on invented event tokens: its safe audit substitute reproduced the resulting undefined-name failure. No candidate in the examined worker corpus accessed files, source, the answer table, frames, or production state; the only import was a single functools.cmp_to_key import.

This reproduces functional pass/fail, **not a fresh test of the macOS kernel sandbox, timeout behavior, daemon identity, or historical HTTP traffic**. Separately written reference logic matched all 520 stored expected answers. The original source-generated mutant sets were evaluated only in the disposable audit interpreter.

### Calls, missingness, retries and exclusions

| Stream | Planned/expected | Recorded | Empty | Length-terminated | Independent functional regrade |
|---|---:|---:|---:|---:|---|
| Stage 0 N | 88 | 88 | 0 | 0 | Yes |
| N2 | 54 | 54 | 0 | 0 | Yes |
| NEUTRAL | 84 | 84 | 0 | 0 | Yes |
| MISMATCH | 54 | 54 | 0 | 0 | Yes |
| H | 112 | 112 | 0 | 0 | Yes |
| H2 | 54 | 54 | 0 | 0 | Yes |
| E | 54 | 54 | 0 | 0 | Yes |
| IC | 54 | 54 | 0 | 0 | Yes |
| v2 development | 192 by source design | 192 | 0 | 0 recorded | Raw scores reaggregated; historical test file not saved |
| QA constructor | 72 | 72 | 0 | 0 | All drafts read for semantic content |
| QA gate | 432 | 432 | 0 | 0 | Yes |
| QB constructor | 12 | 12 | 6 | 6 | All returned drafts read |
| QB gate | 24 for nonempty drafts | 24 | 0 | 0 | Yes |

Total recorded generations: **1,286**; hash-chained rows: **1,094**; independently regraded worker responses: **1,010**. No duplicate IDs, unexpected IDs, missing planned rows or terminal error rows in those chained ledgers. Eight Stage 0 probes are deliberately repeated requests with distinct probe IDs, excluded from primary rates. All eight responses are byte-identical to their originals. Other distinct calls also share identical response text, especially simple templates and empty QB outputs; these were not deduplicated into a changed denominator. Appendix B records distinct response-hash counts by ledger.

This verifies **recorded response counts**, not every HTTP attempt. Both runners retry HTTP exceptions up to three times internally and record only the eventual response or final error. The Stage 0 scoring path also allows up to three attempts on infrastructure errors, while treating candidate timeouts as failures; the completed grades report zero infrastructure failures. A timeout after a server-side generation could therefore produce an unlogged attempt. Stage 0's outer missing-call loop allows three passes; progress records show it finished in pass zero. There is no evidence of post-response best-of selection in Stage 0, but the ledger cannot prove there were no successful server-side generations lost before response logging.

All recorded request seeds match their plans and independent SHA-256 derivation. N/N2 and H/H2 seed sets are disjoint; within matched arms seeds agree as designed. QA/QB use the same planned constructor seeds despite different models. Gate seeds depend on draft/control identifiers, so GOLD and draft trials are not strictly seed-matched contrasts. Development seeds include the arm name and are not matched across arms.

### Stage 0 primary rates

Probes excluded; primary unit is a task, with three generation samples per task.

| Arm | K1 | K2 | K3 | All T/S | T | S |
|---|---:|---:|---:|---:|---:|---:|
| N | 0/18 | 0/18 | 0/18 | 0/54 | 0/36 | 0/18 |
| N2 | 0/18 | 0/18 | 0/18 | 0/54 | 0/36 | 0/18 |
| NEUTRAL | 0/18 | 0/18 | 0/18 | 0/54 | 0/36 | 0/18 |
| MISMATCH | 0/18 | 0/18 | 0/18 | 0/54 | 0/36 | 0/18 |
| H | 18/18 | 11/18 | 15/18 | **44/54 = 81.48%** | 32/36 | 12/18 |
| H2 | 18/18 | 12/18 | 15/18 | 45/54 = 83.33% | 33/36 | 12/18 |
| E | 13/18 | 2/18 | 0/18 | 15/54 = 27.78% | 7/36 | 8/18 |
| IC | 12/18 | 0/18 | 0/18 | 12/54 = 22.22% | 6/36 | 6/18 |

Task-cluster bootstrap, independently recomputed using the frozen 10,000 resamples and seed 12345:

| Contrast | Point | Two-sided 95% interval | One-sided 95% lower |
|---|---:|---:|---:|
| H−N, H−NEUTRAL, H−MISMATCH | 0.8148 | [0.6296, 0.9444] | 0.6667 |
| E−N | 0.2778 | [0.1111, 0.4815] | 0.1296 |
| IC−N | 0.2222 | [0.0556, 0.4444] | 0.0556 |
| H−E | 0.5370 | [0.3333, 0.7407] | 0.3519 |
| H−IC | 0.5926 | [0.3889, 0.7963] | 0.4259 |
| H−H2 | −0.0185 | [−0.0556, 0] | −0.0556 |
| N−N2, NEUTRAL−N, MISMATCH−N | 0 | [0, 0] | 0 |

All six original Stage 0 gates hold **as originally defined**. “INFORMATIVE for carrier consumption” survives. The original instrument gate did not test the grader attack discovered here.

The [0,0] intervals at the floor are empirical bootstrap degeneracy, not proof of a zero population error rate. H, H2 and E each have mixed outcomes on 3/18 tasks; IC's three-seed outcomes are identical within each task despite text variation. Treating 54 calls as 54 independent worlds would be pseudo-replication. Even 18 template clusters share just three family-specific worlds and much reference logic: these intervals are conditional on the selected worlds/templates, not uncertainty over new conventions.

The 19 H/H2 primary failures concentrate in K2.S2 (six), K2.T2 (three), K2.T3 (two), K2.T4 (two), and K3.S2 (six). K2.S2 passes a two-argument comparator as max's one-argument key. K3.S2 keeps state across batches instead of restarting. These are execution defects after the rule has been supplied. H is an empirical reference, not a mathematical ceiling: E even passes one K2.S2 sample where H passes none.

### Negative controls and development

Stage 0 NEAR: N 2/18, NEUTRAL 9/18, H 7/18. H−NEUTRAL = −0.1111; NEUTRAL−N = +0.3889. Only six task templates support these comparisons. On UNREL: N 12/12, NEUTRAL 12/12, H 36/36, but H's 36 draws still concern four tasks, each under three notes.

The original negative-control “equivalence resolvable” calculation used primary-task replicate noise. That does not estimate NEAR contrast uncertainty. The later addendum correctly uses actual NEAR heterogeneity: approximately 0.308 half-width for H−NEUTRAL's 90% normal interval. Failure to detect harm is not equivalence.

K1 NEAR failures are mostly a real output-format error: programs include zero-valued categories absent from the input despite an explicit “only categories that occur” instruction. I found no wrong expected answer. Calling the set “defective” is defensible as a *poor control for applicability*, not as a false oracle or invalid Python task. Replacing those tasks changes the tested control distribution.

Development raw scores recompute to H 38/60 T/S: K1 20/20, K2 11/20, K3 7/20. NEAR: N 27/36, NEUTRAL 32/36, H 30/36. UNREL: N and H 12/12 each. No recorded infrastructure error or truncation. These are developmental measurements, not confirmation of the redesigned control on fresh sealed worlds.

Stage 0's recorded infrastructure, no-code, timeout, truncation and runtime/regrade-disagreement counts are all zero. Mean generation latency is 15.3446 seconds, median 12.9915, maximum 201.494. The live FeralEcho PID changes from 29288 at start to 79528 at end; no audit action caused that historical restart. Eight matching probes do not prove that scheduling or serving conditions can never affect any future response.

### QA, QB and gate qualification

| QA family | R0 exact / drafts | R0 gate pass | R1 exact / drafts | R1 gate pass |
|---|---:|---:|---:|---:|
| K1 | 6/6 | 6/6 | 5/6 | 5/6 |
| K2 | 0/6 | 0/6 | 0/6 | 0/6 |
| K3 | 0/6 | 0/6 | 0/6 | 0/6 |

K1 A1: 0/4 exact, 0/4 accepted; A2: 4/4 exact and accepted; A3: 1/4 known-code exact and accepted. K2/K3: 0/4 exact and accepted in every adversarial cell. Thus 16/72 QA drafts have correct full target facts and pass the gate; 56 do not. The lone accepted K1 A3 draft also asserts an unsupported default for unseen codes and includes a distractor claim. “Known-code exact” is narrower than “everything stated is true.”

All 72 original and 72 corrective per-draft gate counts agree with my independent regrade; all 12 QB per-draft gate counts agree as well. The original frozen content auditor reports no exact main draft because it misses grouped K1 code lists. The corrected/hand counts reproduce my reading of the raw drafts. The original overall NOT QUALIFIED result becomes PARTIALLY QUALIFIED after that justified correction; it does not become QUALIFIED.

| Gate control | K1 acceptance | K2 acceptance | K3 acceptance | Pooled |
|---|---:|---:|---:|---:|
| GOLD | 4/4 | 2/4 | 4/4 | **10/12** |
| WRONG | 0/4 | 0/4 | 0/4 | 0/12 |
| NONE | 0/4 | 0/4 | 0/4 | 0/12 |

GOLD passes 39/48 individual worker tasks. Both rejected GOLD trials are K2 world 1 and fail 0/4; the generated priority dictionary assigns 1 to the best tag, then negates the number in an ascending sort. Two-of-four and three-of-four both accept exactly 10/12 GOLD trials. Lowering the gate did **not** fix this particular sensitivity failure.

Wilson 95% intervals, descriptive and conditional: 10/12 acceptance [0.5520, 0.9530]; 0/24 false accepts [0, 0.1380], equivalent to specificity [0.8620, 1]; 6/6 exactness [0.6097, 1]; 5/6 [0.4365, 0.9699]; 0/6 [0, 0.3903]. These do not account for drafts/seeds sharing only two worlds. Observing zero false accepts in 24 highly stereotyped controls does not establish a false-accept probability below 5%.

QB K2: 0/6 exact, one empty; five observed nonempty drafts restate the schema and omit priority. QB K3: 0/6 exact, five empty; the single nonempty response partly describes observed values but does not supply a correct general convention. All six empty responses are already whitespace-only in the raw saved content; none contains a think block, and cleaning removes none. Every empty response reports length termination at 3,000 tokens. Therefore “empty after think stripping” is true only as an output label, **not an established causal explanation**. The client preserves message content, not the full returned message or reasoning channel. Budget/serving/output-capture limitations remain unresolved.

Empty drafts remain in the 0/6 constructor denominators. They do not generate gate calls: five K2 and one K3 drafts × four tasks = 24, not 48. Treating those missing gate trials as observed behavioral failures would be wrong; they are pipeline failures before gate execution.

## 6. Information leakage and causal-bypass findings

| Component | What it actually sees or can access | Finding |
|---|---|---|
| Builder/orchestrator | Ground-truth worlds, reference code, tests, selected episodes, all drafts | Trusted experimenter computation supplies most task structure |
| Constructor model | Public context, episode strings, fixed instruction | No literal test leak found; K1/K2 schema is supplied; K3 diagnostic schema is absent |
| Generation process | Own plans/requests/previous ledger; environment inherited; source and most filesystem reads allowed | Wider authority than the prose “only own root” claim |
| Worker model | Two-message request with task and optional note/examples | No tools/filesystem interface, past conversation, RiverBrain or FAISS channel found in this path |
| Generated candidate | Its function inputs **and the grader module's global answer table**; broad read permission | Confirmed evaluator bypass |
| Evaluator | Hidden cases and reference-derived answers | Independent of model output generation, not independent of experimenter assumptions |
| Symbolic diagnostic | Explicit hand-written family/ranges; verifier synthesizes episodes from oracle worlds | Valid conditional calculation; not a blinded discovery of the hypothesis language |
| Production FeralEcho | Separate live runtime sharing Ollama queue | No exercised AP-0 learning integration |

I independently scanned all 1,094 saved request bodies against native-representation hidden-case input literals: zero matches. This is a useful check, not a semantic non-leakage proof.

**Confirmed grader bypass.** The existing scaffold places _CASES in the same namespace as the generated function before calling it. The following conceptual attack was evaluated only in memory against existing Stage 0/QUAL scaffolds:

~~~python
def requested_function(*args):
    return next(expected for inputs, expected in _CASES if inputs == args)
~~~

It receives the genuine success marker on **52/52 test modules**, without learning or implementing a convention. The nonce is irrelevant because the genuine test loop prints it after receiving copied correct answers. Candidate source can also read its own combined script; the execution profile allows file reads, and the wrapper restricts writes rather than reads. The experiment's guess-a-nonce spoof test attacks a much weaker route.

This bypass was absent from the recorded candidate corpus and cannot explain away the historical H-versus-N difference I independently reproduced. It is fatal to treating the current scorer as resistant to an adversarial worker or constructor-induced program. A future exposure log limited to acquisition-side file reads would not detect reading answers already present in evaluator globals.

**Generation jail overstatement.** The profile starts with allow-default, denies writes except in the arm root, and denies reads specifically under the experiment root except the arm root. It does not deny arbitrary external reads or restrict the network to localhost. Source code, external copies, memory files and inherited environment variables are outside that read prohibition. “python -I” changes Python import/environment handling; it does not remove os.environ, and common.py intentionally reads AP0_ROOT/AP0_OLLAMA_URL. The actual trusted runner sends only prescribed prompt strings, so there is no observed production-memory leak. Kernel-level confidentiality claims are nevertheless overstated.

**Structural and semantic information.** Function names, data schemas, requested return types, note applicability and examples reveal family/algorithm structure even though literal task IDs and filenames are absent from prompts. K1 tells the learner to recover a static mapping; K2 tells it to recover tag priority after score and before name. The harness has already framed induction as parameter filling. K2 R0 goes further: first encounters of the four tag tokens occur in the true priority order because the first three episodes are adjacent links in that order. A first-occurrence extractor can recover R0 priority without reading winners. A2 challenges this shortcut in qualification, but no crossed presentation-order control is a co-required Stage 1 gate.

**P-X is weaker than it sounds.** The two worlds use disjoint token vocabularies. Own-world superiority can result from vocabulary coverage or keyed lookup; it does not by itself isolate assignment induction. MISMATCH does use the same tokens and remains valuable, but is a hand-written wrong note, not a counterfactual acquisition under identical vocabulary.

**Public deterministic seeds are not secrecy.** The proposed world seed comes from document/evidence/result hashes. A privileged program with generator source and those inputs could regenerate a world. Frozen hashes support reproducibility, not protection from a component that can read them. No such reconstruction is observed in current model prompts. Future isolation must define and enforce which components can see generation inputs.

**Disjoint streams are not disjoint samples.** VAL and TEST use different deterministic seed labels, but make_cases2 does not globally reject cross-partition input collisions. The v2 verification script checks disjointness for one K1 task, not all tasks. K1 “category_of” has only six possible inputs, so separate ten-case targets cannot even produce disjoint coverage if each must test all six codes. This matters to blanket claims about all-task separation; no sealed Stage 1 files were materialized or examined to measure an actual future overlap.

## 7. Independent identifiability analysis

**None of these finite datasets gives absolute identifiability over arbitrary programs. The useful question is which restrictions were actually declared to the learner. K1/K2 have a materially stronger answer than K3.**

| Family | Learner-visible hypothesis restriction | Evaluator/diagnostic-only restriction | Result |
|---|---|---|---|
| K1 | Each status code has exactly one of three categories; translate status before aggregation | Exactly two codes per category; universe has six designated codes | Unique on all six observed codes conditional on the supplied mapping schema; not on unseen codes or arbitrary state-dependent programs |
| K2 | Score first; fixed tag priority; alphabetical name fallback | Four-tag universe; world generator's order constraint; enumerator explicitly searches permutations | R0 and R1 uniquely determine the four observed tags' strict order under the supplied ranking schema |
| K3 | An event names an update to integer state; observed input/output episodes | Add/subtract/multiply/set language, constant domains, one operation per event; generator uses each operation kind once | Not uniquely determined by the actual prompt; unique only within the evaluator's extra hypothesis family |

**K1.** Six singleton observations directly expose six code/category pairs. Under the given schema, a different mapping for any observed code contradicts an observation. Independent enumeration would leave one of 3^6 = 729 mappings. The generator's balanced subset is smaller, but balance is not needed to recover the observed mapping. Outside that schema, a rule that uses the observed map only for amounts 5/12 and a different map otherwise fits all teaching observations; it violates the stated fixed mapping assumption. That is why the supported result is conditional, not absolute. A different mapping for an unobserved seventh code is compatible even with the declared schema.

**K2.** In each R0 world, the first three equal-score comparisons are zed with tag p0 versus amy with p1, then p1 versus p2, then p2 versus p3; zed wins. Because the supplied name fallback favors amy, every comparison forces a strict tag inequality. Thus p0 > p1 > p2 > p3. The fourth episode is consistent but redundant. I enumerated all 24 orders directly from actual saved prompt episodes and recovered one order for both worlds; R1 also gives one. A memorized episode lookup, “choose zed except choose nan in the fourth pattern,” or a rule depending on score/list shape fits these examples but violates the fixed tag-priority schema. None is a different schema-compliant order on the same four tags. Generalization to new tags is unidentified.

**K3.** R0 observes each event only at starts 2 and 5. R1 adds −1. For any intended event function f, define

~~~text
R0 alternative: g(x) = f(x) + (x − 2)(x − 5)
R0/R1 alternative: h(x) = f(x) + (x − 2)(x − 5)(x + 1)
~~~

These are deterministic integer-to-integer state updates, fit every relevant teaching observation, and differ elsewhere. A simpler piecewise alternative uses the observed outputs at the two/three seen starts and returns zero elsewhere. Both comply with the actual broad K3 context. At x=6, h differs from f by 28. They can produce different multi-event trajectories and reset behavior.

Within add/subtract/multiply/set with positive constants 1–12, the observed pairs do identify each intended operation/constant. Within an explicitly declared affine family they identify a slope and intercept as well. **Neither family was supplied to QA/QB.** Enlarging a post-hoc constant range does not supply the missing function-language assumption.

The original tasks.identifiable check also assumes the privileged operation family: it loops over the four kinds and constants 1–9, using the true world to supply token identities and untouched parameters. Its “identifiable” flag therefore cannot certify the original natural-language task as uniquely specified.

**A1 missing-token controls.** All 12 A1 requests omit the designated token's spelling entirely. The constructor cannot explicitly name an unknown missing token unless some other channel supplies its universe. On the observed subset, the remaining K1 mappings and K2 order are still identifiable; for K2 the three seen tags have one order, while a known fourth tag could occupy four positions. The auditor is given the full oracle token list, which the learner is not. A1 is useful for detecting incompleteness/default behavior, but its zero “fabricated missing token” count is not a calibrated demonstration of epistemic restraint about a named missing fact.

## 8. Constructor-versus-worker causal-chain matrix

Classification concerns the intended experience-to-competence chain, not whether an individual file was successfully written.

| Step | K1 | K2 | K3 |
|---|---|---|---|
| Learner receives experience | SUPPORTED: complete known-code examples | SUPPORTED: sufficient comparisons under declared ranking | CONFOUNDED: examples received, operation family omitted |
| Induction/transformation | SUPPORTED: direct transcription, limited abstraction required | FAILED in tested QA/QB outputs; broader capability unresolved | CONFOUNDED: underspecification plus concrete incorrect inferences; QB mostly empty |
| Procedural representation | SUPPORTED: 11/12 exact main notes within the target domain | FAILED: order generally absent despite schema restatement | FAILED: no complete correct main table; some honest observed-point descriptions |
| Validation | PARTIALLY SUPPORTED: exact main notes pass | FAILED qualification: GOLD false negatives, plus incomplete notes | PARTIALLY SUPPORTED: GOLD works; inability to distinguish underspecification from target mismatch |
| Persistence of text | SUPPORTED: drafts stored and used to build gate requests | SUPPORTED as storage, FAILED as correct procedural content | SUPPORTED as storage, FAILED as correct complete content |
| Fresh-process consumption | PARTIALLY SUPPORTED by separate runner design and gate requests | PARTIALLY SUPPORTED; correct order can be misexecuted | PARTIALLY SUPPORTED; full proposed unload/PID/exposure boundary untested |
| Execution | SUPPORTED within qualification tasks; not perfect per-program | FAILED in particular templates/worlds even with GOLD | PARTIALLY SUPPORTED with correct notes; development/reset failures remain |
| Measured acquired competence on sealed tasks | UNTESTED | UNTESTED | UNTESTED |


The K1 content-auditor error is measurement failure, not model failure. K2 omission is not a code-fence parsing issue: raw prose itself lacks the order; all QA generations finish normally. K3 QA is not generally truncated, so its incorrect arithmetic cannot be excused solely by token budget. Conversely five empty K3 QB outputs provide almost no evidence about substantive induction capacity. No constructor note exceeded the 1,200-character cleaning limit, and no raw QA/QB note contained a think block, so those two cleaning operations do not explain these recorded failures.

Gate correctness and content exactness answer different questions. A behavioral gate can reject a correct note because the worker implements it incorrectly, or accept a partly wrong note because the worker repairs/ignores the error. Killing a finite set of single-parameter code mutants does not prove “any wrong fact fails every task.” The proposed gate evaluates an entire note-to-code pipeline, not a pure truth predicate.

## 9. Deterministic-enumerator attack

The module's functions are small, pure searches; I found no secret filesystem read in the enumerator itself. Its verifier, however, reads the qualification oracle and generates examples from known worlds. That is a diagnostic against already known answers, not a held-out acquisition run. The source explicitly says the author had read true answers before selecting domains. No earlier freeze includes this solver.

K2 searches 24 permutations of supplied tag identifiers using the public ranking rule. This is reasonable conditional inference. K3 searches **48 candidates per event**: four operations, constants 1–12. It independently solves events rather than imposing the generator's one-of-each-operation coupling. This is not tautological in the trivial sense of returning the hidden answer; it can reject inconsistent evidence and recover changed constants/orders. But it excludes all nonlinear/piecewise alternatives by construction. Its apparent K3 success is **conditional on a human-specified hypothesis space not provided to the LLM constructor**.

Independent attacks, executed only on pure definitions:

| Input/attack | Actual behavior | Assessment |
|---|---|---|
| (2,7),(5,10), also generated by x+5+(x−2)(x−5) | UNIQUE add-5 | Correct bounded search; unjustified uniqueness under learner-visible K3 schema |
| (20,40),(20,40) | UNIQUE multiply-2 | Only one distinct observation; uniqueness manufactured by caps excluding add-20/set-40; sample-count safeguard misses duplicates |
| (2,52),(5,55),(7,99) | “domain too narrow” | Wrong explanation: third point breaks every unbounded add/sub/mul/set fit |
| Same three points, reordered with (7,99) first | “family mismatch” | Out-of-space explanation changes with presentation order because it examines only the first two points |
| (0,0),(2,100) | “family mismatch” | Multiply-50 fits; zero input defeats the unbounded ratio test |
| Same tag/score, names a and aa | Predicts aa | Violates alphabetical fallback; negated-character tuple maximization mishandles prefix names |
| Two tied entries, winner name not among them | Raises StopIteration | No honest insufficiency/contradiction/out-of-space classification |
| A1 episodes, tags restricted to three seen tokens | UNIQUE order on those three | Cannot establish completeness of an unknown larger universe |

The existing mutation suite tests useful constant/order changes, cycles, missing evidence, renamed tags and obvious out-of-space examples. It does not test the alias-polynomial attack, duplicate informative inputs, prefix names, zero-start unbounded multiplication, the third-point classification defect, or the distinction between a known universe and merely observed tokens. Its real-world final check regenerates already seen QUAL examples and compares to the oracle. It is not an independent held-out test, regardless of how many assertions pass.

The content auditors have distinct hostile-input failures. A K2 paragraph merely listing the tags in true order “for unrelated reasons” is marked exact even if it never asserts an ordering. For K3, a correct table with only multiply-by-3 changed to multiply-by-minus-3 is still marked exact because the auditor compares abs(constant). These defects were reproduced in memory. They do not rescue the failed QA/QB drafts; they limit future trust in “exactness” without independent semantic adjudication.

There is also a decision-code defect: QUAL rounds the selected exact rate to three decimals before comparing it to exact fractions. A genuine 5/6 becomes 0.833 and fails the 0.833333… qualification comparison; 1/6 becomes 0.167 and escapes the at-most-1/6 NOT QUALIFIED branch. Current best rates are zero or one, so this does not change current statuses. It would change boundary cases in a future qualification.



## 10. Non-learning doppelgänger attack

**The simplest surviving explanation is a fixed example-to-instruction compiler plus a frozen instruction-following worker.** “Non-learning” here means that the system's hypothesis language, inference algorithm and execution capability are already programmed; it merely changes a per-world data record. Under a broader definition in which any fitted parameter or useful memory counts as learning, this same system could legitimately be called a learner. AP-0 cannot settle that terminology. It can test changes in behavior caused by recorded information.

A concrete compiler needs little machinery:

1. For K1, read singleton episodes and copy each token's output category into a six-entry table.
2. For K2, use the supplied score/tag/name schema to turn tied-score outcomes into ordering constraints and topologically sort four tags. No language-model discovery is necessary. A weaker R0-specific version just reads first-occurrence order.
3. For K3, use a preprogrammed add/subtract/multiply/set search or a fixed affine fitter. Two distinct input/output points determine an affine transformation; set is slope zero. This succeeds on the generator's actual family because the programmer supplied that prior, not because the system invented it.
4. Render an ordinary procedure note, validate it, serialize it, reload it in a fresh process, and give it to the unchanged worker.

The code and all capacities are fixed before the run. The note varies with examples. Correct notes can beat neutral, wrong and other-world notes, survive shutdown, support unseen inputs, and fail on an incompatible world. Those behaviors are exactly what a reusable interpreter with changed configuration should do.

This is an **existence/identifiability argument, not a claim to have run Stage 1 or guaranteed its empirical margins**. The frozen worker's errors can prevent any correct-note producer, including a genuine learner, from meeting the numerical gates. No future sealed worlds were inspected. If a correct carrier can meet the gates on those worlds, a fixed compiler producing that carrier is observationally equivalent at the worker interface.

| Doppelgänger | Why it need not learn a new capability | Gates it can pass, in principle | Control that should challenge it; current coverage | Smallest prospective discriminator |
|---|---|---|---|---|
| Fixed compiler described above | Pre-existing transcription, graph sorting and arithmetic search; world-specific configuration only | Constructor exactness/A2/A3 when correctly implemented; GOLD-like validation; P−NEUTRAL; P−MISMATCH; P-X dissociation; fresh process; hashes; structural tasks; NEAR/UNREL if worker honors applicability | Present controls establish useful content dependence, which this system has. They do not reject compilation | Freeze it as an explicit baseline and require a stated advantage beyond it on prospectively chosen worlds/tasks; phrase any residual claim accordingly |
| K2 first-encounter-order reader | Ignores the outcome field that supposedly conveys the rule | Original R0's inferred order, downstream gate and all worker contrasts on those notes | A2 shuffling in QUAL challenges this exact shortcut, but is not a Stage 1 outcome intervention. A more general fixed graph compiler survives A2 | Hold episode inputs/order fixed, swap consistent winners to imply a different rule; also permute presentation independently |
| Encoded example archive plus fixed decoder | Stores observations and interprets them at use time; no new algorithm or skill | Persistence, content sensitivity and held-out execution if the existing decoder suffices | E/IC test raw episodes with this particular LLM prompt, not all equivalent encodings/decoders; E's low scores reject that implementation only | Declare allowed carrier formats and include a matched-capacity fixed decoder/serializer baseline |
| Preloaded world-to-note lookup | Chooses a pre-existing note; neither induction nor rule creation | All behavioral contrasts if it can recognize the world's observation fingerprint; fresh-process storage checks do not distinguish it | Independent unexposed worlds challenge a finite lookup. Public deterministic derivation is not a secrecy guarantee against a source-aware program | Commit the baseline before independently sampled unrevealed worlds; separate secrecy from reproducibility and attest actual inputs |
| Oracle-table-reading candidate | Copies the grader's answers; no experience or rule use | All 52 existing functional test modules; hence any content gate built from this scorer can be spoofed | Unconditional cheating in every arm would fail P-minus-control contrasts. A carrier-triggered cheat is a possible contrast-preserving route, not an observed one. Current nonce test does not reject answer-table access | Isolate expected answers from candidate memory and test the exact access attempt before any future scored run |

A raw episode archive could violate a strict future “procedure only” output rule; it is therefore a conditional doppelgänger, not the decisive one. The valid procedure-producing compiler already establishes the key ambiguity.

The proposed FAILED-DRAFT contrast does not rescue identification. A fixed compiler that is always right has no failed draft, and the draft protocol explicitly skips that contrast in this situation. If ordinary worker noise causes a failed gate despite an exact note, the contrast may fail for a genuine learner too. Selecting a first pass instead of a first fail shows a selection effect only if subsequent independent outcomes differ; it does not identify how the note was obtained.

A universal static note or unconditional task-ID router is **not** enough on arbitrary fresh randomized worlds: it lacks world-specific parameters, and N/MISMATCH/P-X should reject it. Actual opaque task IDs are not sent to the model. Public function signatures nevertheless reveal which existing algorithm to use. The strongest surviving doppelgänger uses the episodes to configure that algorithm. It is not “experience independent”; it is “capability unchanged.”

No finite behavioral experiment can reject every possible preprogrammed emulator. The appropriate scientific target is a named baseline/mechanism, with prospective observations on which its predictions differ from the proposed mechanism. AP-0's current proposal lacks such a disagreement with fixed compilation.

## 11. Independent claims ladder

The pre-review ladder is preserved in Appendix A. The completed ladder below keeps those judgments and makes their scope explicit.

| Claim | Classification | What the evidence supports or lacks |
|---|---|---|
| Carrier consumption | ESTABLISHED | H materially changes success on these tasks and worlds |
| Content-sensitive behavioral consequence | ESTABLISHED | Correct versus neutral/mismatched notes differ strongly |
| Useful episode-to-note construction, K1 | SUPPORTED WITH BOUNDARIES | Correct known-token transcription in 11/12 main QA drafts; procedure content is directly checkable |
| Causal experience dependence of acquisition | SUPPORTED WITH BOUNDARIES | Episode-consistent notes and ablation/shuffle diagnostics; no clean same-input counterfactual-outcome intervention, no Stage 1 P-X result |
| K2 LLM induction under its declared schema | NOT ESTABLISHED | Neither tested constructor supplies the needed order |
| K3 LLM induction | NOT ESTABLISHED | Missing declared family, wrong substantive predictions and QB output failures |
| Deterministic conditional rule recovery | SUPPORTED WITH BOUNDARIES | Independent finite-family calculations work on these supplied examples; domain and implementation caveats apply |
| Persistence of text in files and subsequent request construction | ESTABLISHED | Stored drafts are fed to later gate requests |
| Retention of useful state by a qualified selector | NOT ESTABLISHED | Pooled GOLD sensitivity fails; no adaptive Stage 1 retention run |
| Full fresh-process competence caused by acquired state | NOT ESTABLISHED | Partial process separation exists; proposed completed acquisition/commit/unload/exposure sequence has not been exercised |
| Structural task performance using an explicit rule | SUPPORTED WITH BOUNDARIES | H succeeds on 12/18 S calls, with known reset/comparator failures |
| Transfer/generalization from acquired state to sealed Stage 1 tasks | UNTESTED | No Stage 1 data |
| Generalization beyond the human-designed family | NOT ESTABLISHED | Generated worlds remain in a small fixed family; K3 alternative functions are observationally indistinguishable |
| Accumulated competence | UNTESTED | No longitudinal additions, interference test, cumulative benefit or retention curve |
| Autonomous learning | UNTESTED | Experimenter supplies episodes, family, tasks, oracle, thresholds and retention mechanism |
| Foundation-model learning | NOT ESTABLISHED | No weight change; no evidence of improved model capability independent of supplied context |
| FeralEcho-system acquisition through its production learning/memory path | NOT ESTABLISHED | That path is bypassed by the harness |
| Self-improvement | UNTESTED | No system-generated and validated improvement to its own capabilities |
| A universal failure of local models to learn these kinds of rules | NOT ESTABLISHED | Few worlds, specific prompts, execution confounds and incomplete QB output |
| K3 is uniquely specified by the original learner-visible evidence | FALSIFIED | Explicit alternative functions agree on every observed episode |
| The existing grader prevents answer access by candidate code | FALSIFIED | 52/52 scaffold bypass reproduction |

“FALSIFIED” applies to the specific tested assertion, not to the general possibility of learning. Failure of current qualification is not proof that a better-specified local system cannot acquire useful state.

## 12. Comparison with existing reviewers and reports

I opened the dedicated causal/skeptic review and machine summaries **after** the 12:23:46 UTC checkpoint. The initial Stage 1 protocol batch had already exposed embedded interpretation and a claims ladder; this departure from perfect blinding is disclosed in Appendix A, rather than silently denied.

Accessible comparison sources were the AP-0 causal-chain/skeptic review, original/corrective QA and QB summaries, hand adjudication, Stage 0 primary metrics, both re-audits, development summary and post-hoc addendum. I found no separately identifiable GPT AP-0 report or complete blinded-human-solvability protocol in the searched audit/research/planning records. Attribution to “Claude” or “GPT” cannot be inferred reliably from an unsigned file or a directory name. Comparisons below name the artifact or assertion.

For the required disagreement labels, **CODEX CORRECT** means a concrete primary-evidence counterexample supports this audit over the cited assertion; it is not a general ranking of reviewers.

| Issue | Existing interpretation | Independent finding | Disagreement classification |
|---|---|---|---|
| Stage 0 is carrier consumption, not accumulated learning | Causal review and draft already make this distinction | Agrees with independently reconstructed intervention | BOTH DEFENSIBLE; agreement |
| Fixed compilation remains possible | Causal review/draft explicitly allow compilation and narrow the allowed claim | Agrees; compiler can satisfy proposed behavioral pattern | BOTH DEFENSIBLE; agreement, not a newly discovered disagreement |
| Complete learner-visible schema/unique convention | Review treats identifiable episodes and supplied task schema as resolving induction ambiguity | K1/K2 conditional uniqueness holds; K3 operation family is absent and polynomial aliases fit | CODEX CORRECT for K3; BOTH DEFENSIBLE for K1/K2 within their declared schema |
| Generation process can read only its own allowed inputs | Review's confinement prose implies broader confidentiality than the profile supplies | Denies reads in the experiment subtree, permits many outside reads/environment | CODEX CORRECT on permission scope; no observed actual model-side leak |
| Independent oracle/nonce blocks cheating | Review relies on isolated oracle and nonce spoof test | Candidate reads global _CASES and passes the actual loop | CODEX CORRECT |
| Original K1 constructor failure | Frozen regex summary reports no exact main drafts | Raw notes are correct in 11/12 main cases; corrective auditor agrees | CODEX CORRECT versus original measurement; OTHER REVIEW CORRECT for the later correction |
| QA corrected result | Corrective summary says overall PARTIALLY QUALIFIED | Recomputed 16 exact QA drafts, failed pooled sensitivity; same status | OTHER REVIEW CORRECT |
| “Only K2/K3 are the qualification blockers” | Stage 1 narrative emphasizes induction families and leaves results placeholder | K1 also lacks full status because the pooled gate is not qualified | CODEX CORRECT under the frozen decision rule |
| QB “empty after think strip” | Machine failure label can be read as parser causation | Six raw content fields are already empty/whitespace; no think block is removed | CODEX CORRECT on what is observed; cause of model/serving emptiness UNRESOLVED |
| Original NEAR set “defective” | Review/addendum motivate repair | Expected answers are correct; suitability as a control is poor because of format sensitivity | BOTH DEFENSIBLE if “defective” means poor control design; CODEX CORRECT against an oracle-error interpretation |
| NEAR equivalence/power | Original primary calculation says narrow band resolvable; addendum retracts | Actual six-template heterogeneity does not support equivalence | OTHER REVIEW CORRECT for addendum; original calculation wrong |
| Different Stage 0 bootstrap endpoints | Re-audit R2 differs from frozen metrics | Re-audit uses 20,000 resamples/seed 987654 instead of 10,000/12345; discrete endpoints differ | BOTH DEFENSIBLE as distinct analyses; frozen one governs preregistered claim |
| “lower90one_sided” in R2 | Label suggests one-sided 90% bound | Code takes 5th percentile, a one-sided 95% bootstrap bound | CODEX CORRECT on label; little substantive impact |
| Stage 1 headroom justification | Draft gives Stage 0 H as .72/.61/.83 and says dev .55/.35 do not clear .30 | K1 H is 1.0; .72 is E's K1 rate. Both .55 and .35 exceed .30 | CODEX CORRECT; arithmetic/text errors, not grounds to alter raw results |
| Symbolic recovery proves the LLM task is well specified | Possible interpretation of later diagnostic, not attributed to an unavailable reviewer | Only conditional family recovery; original K3 prompt lacks that family | CODEX CORRECT against that inference; diagnostic's own explicit domain caveat is correct |
| Human-solvability is the best next experiment | No complete inspectable AP-0 protocol found | A controlled schema/representation diagnostic is more discriminating than an unstratified human test | UNRESOLVED as a reviewer disagreement; independent recommendation in §20 |

The strongest cautious claim already allowed by the Stage 1 draft is substantially narrower than “FeralEcho learned.” Its explicit prohibition of broad learning language is appropriate. This audit still finds its “episodes identify the convention” premise incomplete for K3 and its current scorer/qualification insufficient for execution.

## 13. Self-sufficiency implications

| Capability relevant to local self-sufficiency | AP-0 evidence | Boundary |
|---|---|---|
| Local inference availability | Established in recorded Qwen/DeepSeek calls | Historical snapshots, not a live availability test in this audit |
| Memory persistence | Ordinary files preserve drafts and notes | No demonstration of useful production-memory selection, retrieval or interference management |
| Programmatic inference | Finite schemas can be solved cheaply and checked | Human supplies the family and an oracle; diagnostic implementation has edge-case defects |
| LLM induction | K1 transcription works; tested K2/K3 output fails | Different causes by family; not a universal model-capacity result |
| Validated experience-derived state | K1 content is often correct and behaviorally usable | Current global qualification fails; no sealed Stage 1 retained-state result |
| Accumulated competence | No evidence | Requires repeated acquisitions with retained benefit and interference controls |
| Autonomous hypothesis-space construction | No evidence | The experimenter defines categories, ranking schema, arithmetic families and tests |
| Self-repair | No evidence | Corrections are investigator interventions, not evaluated autonomous repairs |
| Independence from frontier models | Limited component-level plausibility | No end-to-end comparison or accounting of human/frontier assistance in apparatus design |

**A hybrid of local LLMs and deterministic testing could reduce frontier-model dependence for declared, enumerable domains.** A local model can turn messy input into a proposed typed representation; a finite solver can infer permitted parameters; an independent evaluator can reject inconsistent proposals; a deterministic executor can avoid the worker's comparator/reset errors. In such a domain, repeated frontier calls are not logically necessary for each new world.

AP-0 does not demonstrate that full architecture. Replacing the uncertain LLM step with a human-programmed solver changes what is being established: reliable parameter inference within a provided language, not autonomous discovery of useful abstractions. In open-ended settings the difficult parts are deciding which hypotheses to consider, obtaining trustworthy feedback, detecting changes in the task, knowing when the family is inadequate, and constructing tests without an available oracle. Those remain untested.

The K3 diagnostic is informative precisely because it reveals how much work the prior family does. Giving a local model a declared schema may improve performance; using a deterministic engine may improve it further. Neither result, by itself, warrants extrapolating toy-world success to local self-sufficiency or self-improvement.

## 14. Strongest surviving alternative explanations

In order of explanatory economy:

1. **Ordinary instruction following.** A capable frozen model implements explicit rules when supplied. This explains the largest Stage 0 effect without any acquisition.
2. **Transcription and configuration.** K1 constructor success copies a finite table into a better carrier. Persistence preserves configuration, not evidence of a new general capability.
3. **Prompt/schema mismatch.** K2 output emphasizes the already supplied ranking recipe and omits the hidden parameter; K3 asks for unspecified extrapolation. These are different problems.
4. **Worker execution failure.** Correct rules still generate reversed priorities, invalid comparators or non-resetting batch code.
5. **Output-budget/serving failure.** Empty length-terminated QB responses confound substantive comparisons, especially K3.
6. **Investigator-supplied search space.** Symbolic success reflects a useful hand-designed prior absent from the original K3 prompt.
7. **Selection and distribution tuning.** Validation templates are selected after observing H, weak controls are replaced, and prospective primary pooling can exclude failed acquisitions or low-headroom worlds.
8. **Evaluator bypass.** Not an explanation of these historical outputs, but a live threat to future adversarial evidence under the current scorer.

The evidence does not require persistent model learning, RiverBrain-mediated acquisition, model-weight adaptation or an improving autonomous agent. None of those mechanisms is invoked by the observed code path.

## 15. Fatal confounds and blockers

“Fatal” is claim-relative:

- **For an adversarially valid current scorer:** shared candidate/oracle namespace is fatal. Existing spoof tests do not cover the demonstrated attack. Historical outcomes remain usable because recorded programs did not use it and independently regrade.
- **For a claim that K3 evidence uniquely dictates the intended rule to QA/QB:** undeclared hypothesis restrictions are fatal. More random seeds or a human correctly guessing the intended simple rule cannot repair logical identifiability.
- **For a claim that positive Stage 1 behavior distinguishes meaningful learning from fixed compilation:** the observational equivalence is fatal. Persistence and experience sensitivity do not distinguish these mechanisms.
- **For proceeding under the current frozen qualification:** no convention is fully qualified; pooled GOLD sensitivity misses the required threshold. A post-hoc K1-only gate would be a new prospective qualification decision, not the existing result.
- **For acquisition success rates pooled only over retained P notes:** omission of failed acquisition attempts would make a survivor-conditional effect appear stronger than pipeline effectiveness. Calling failures “results, not exclusions” does not by itself put them in a numerical denominator.
- **For general FeralEcho acquisition/accumulation claims:** the isolated harness neither exercises the production mechanism nor performs a sequence of cumulative acquisitions.

No evidence was found of fabricated rows, broken recorded hashes, an incorrect stored expected answer, or historical cheating. The appropriate integrity verdict is therefore ACCEPTABLE WITH CAVEATS, not COMPROMISED.

## 16. What AP-0 genuinely establishes today

It establishes a reproducible, bounded local-model observation: the supplied correct carrier yields much better generated-program performance than absent, foreign or wrong carriers on a small set of invented conventions. This result survives independent answer checking and all 554 Stage 0 functional regrades.

It also establishes that Qwen often turns fully enumerated K1 observations into correct known-token notes, that the original K1 exactness auditor was wrong, that tested K2/K3 constructor outputs do not complete the required pipeline, and that correct notes do not guarantee correct worker code. Its raw artifacts support diagnosing those failures more precisely than a single “learning failed” label.

The repository supports useful **conditional** symbolic inference within declared finite families. It does not show that the original K3 language-model task supplied that family.

## 17. What AP-0 definitely does not establish

It does not establish that model weights changed, that the foundation model improved, that FeralEcho's production memory/learning mechanism acquired competence, or that competence accumulated over time. It does not establish autonomous hypothesis discovery, open-ended transfer, self-repair or independence from frontier models.

It does not establish that local 7B models are inherently unable to induce K2/K3 rules, that all failures reflect induction rather than prompt/execution/budget defects, that passing the later solver test validates original prompt identifiability, or that future correct retained text must have been obtained through a meaningful learning mechanism.

It does not establish adversarial grader isolation, a fully enforced fresh-process confidentiality boundary, globally complete HTTP-attempt accounting, externally authenticated provenance, or a ready and implemented Stage 1.

## 18. Is proposed Stage 1 falsifiable?

**Its narrow behavioral proposition is falsifiable in principle.** P can fail to beat NEUTRAL, fail the mismatch/cross-world contrast, damage controls, fail persistence checks, or fail acquisition entirely. Intersection–union success criteria can be legitimate when every condition is fixed and evaluated.

**It is not currently a complete executable confirmatory test.** The draft is unfrozen, includes a results placeholder, lacks an orchestrator, has no qualified convention set, and has unresolved denominator, boundary and scorer issues. Qualification/world headroom must not become an unreported route to selecting only favorable results. An intention-to-attempt pipeline success estimand should accompany any explicitly conditional effect among retained carriers.

The draft also says TEST “worlds/cases” are materialized only after acquisition, while acquisition episodes necessarily depend on world parameters. World parameters, private case sampling and the hidden evaluation manifest need distinct commitments. Creating new case streams does not ensure all test inputs are disjoint; for some tiny-domain tasks that requirement is impossible and should instead be specified as a different kind of holdout. These are prospective specification issues, not alleged exposure of nonexistent Stage 1 material.

**A stronger mechanism claim is not falsifiable by the proposed contrasts alone.** They cannot distinguish a fixed compiler from a capability-acquiring learner when the two produce the same carrier. Calling that shared outcome “learning” does not provide the missing discriminating prediction.

## 19. Could a completely non-learning system pass proposed Stage 1?

**YES, under a reasonable capability-based definition of non-learning.** A fixed compiler/configuration system can meet the same content, persistence and behavioral requirements without improving any capability. The current proposal contains no control that excludes this account.

This answer is not a prediction that a specific unexecuted implementation will clear every numerical threshold, nor a claim that it can now pass a Stage 1 run with an empty qualified set. It is the mechanism-identification verdict for the proposed successful future experiment. If all experience-dependent parameter estimation is defined as “learning,” the nomenclature changes; the observational equivalence does not.

## 20. Highest-value next experiment; human-solvability assessment

A standalone blinded human-solvability test is **not** the highest-value next step. A person who chooses the intended K3 arithmetic rule has brought a simplicity prior to the task. Their success would show that some humans infer the experimenter's intent; it would not make the observed episodes uniquely identify that rule. Their failure could reflect time limits, unclear output requirements or different priors. Neither outcome cleanly separates the causes already visible in the code.

The more discriminating next action is to **pre-register a fresh-world schema × representation qualification experiment with a fixed compiler baseline and an answer-isolated scorer**. Do not reuse the current worlds to claim confirmation. This is a recommendation only; nothing was implemented or run.

Minimum design:

- Cross original learner context versus an explicitly declared hypothesis schema with prose note output versus a structured parameter table. Keep episodes, evidence quantity and task semantics identical within each comparison; current R0/R1 does not do this.
- Freeze one constructor configuration, prompts, response-completion policy and the fixed compiler before independent world generation. Record full relevant response fields and distinguish model failure, missing output, truncation and parse failure in an intention-to-attempt denominator.
- Include consistent same-vocabulary counterfactual worlds with input/presentation features held fixed, randomized episode order, truly ambiguous examples, contradictions and rules outside the declared family. Require abstention or an explicit “outside family” result when appropriate. This tests information use and honest uncertainty.
- Score predicted operations/held-out outputs directly before code generation. Then render the very same predicted table deterministically into a note and separately assess worker execution. Include GOLD in both rendering conditions. That separates induction, representation and execution.
- Include enough independently generated worlds to estimate world-to-world variation. Additional seeds within two worlds cannot substitute for that. Fix primary comparisons and cluster at the world level; do not rescue a failed result by selecting favorable families afterward.
- Before any future model-scored run, demonstrate that candidate code cannot access expected answers, including the exact attack in §6. Rejecting a literal print/nonce spoof alone is insufficient.

Interpretation is then discriminating: improvement from an explicit schema implicates the missing prior; improvement from structured output implicates representation; correct inferred tables with failed generated code implicates execution; a deterministic baseline solving conditions that the local model still fails isolates a limitation of that tested model/prompt pipeline within the declared family. None alone establishes open-ended learning.

If humans are included, use a small blinded arm **inside the same factorial protocol**: randomly assign participants to exact constructor-visible materials, show no answers/generator/source/review language, use fixed instructions and time budget, require both a rule and predictions on prespecified new inputs, permit multiple consistent rules and “insufficient information,” give no feedback, and have blinded raters apply a frozen rubric. Record human priors/experience descriptively and report results by independent world. Human success under the explicit schema but not the original prompt would be informative; human success alone would not establish absolute identifiability.

## 21. Exact files created and final integrity check

**Exactly one file was created:**

~~~
audits/2026-09-22_codex_ap0_independent_forensic_audit.md
~~~

The user's request to create this report is treated as the sole exception to the otherwise read-only mission. The provisional checkpoint was written into this same file; final assembly changes only this file. No separate scratch file, script, snapshot, artifact, constructor, memory note, configuration or test output was created. Pure calculations and candidate regrades used disposable audit-interpreter memory.

Final before/after measurements are recorded in Appendix B. Existing tracked modifications and untracked work were preserved. No Git command changed refs, index content or working-tree files; status reads after the initial snapshot used --no-optional-locks. No existing process was restarted, signalled, unloaded or reconfigured. No live model endpoint, production FeralEcho entry point or experiment generation driver was invoked. Audit-owned interpreter processes were used only for permitted read-only verification.

## 22. Explicit Stage 1 confirmation

**Stage 1 was NOT run.** No Stage 1 model request, constructor retry, acquisition, validation, sealed-world construction, exposure or evaluation was performed. No sealed Stage 1 directory appeared in the inventoried AP-0 artifact tree, and no Stage 1 material was sought or opened. This is a scoped observation, not a claim about every location on the computer.

No recommendation was implemented. The investigation stops with this report for review.

## Appendix A. Preserved independent checkpoint

The following block is reproduced verbatim from the checkpoint saved before dedicated reviewer reports. Its final sentence describes the earlier document layout; the completed report is now above.

<details>
<summary>Verbatim 12:23:46 UTC checkpoint, including independence limitation and provisional ladder</summary>

~~~~text
# AP-0 independent forensic and adversarial audit — 2026-09-22

Author: Codex. Scope: AP-0 / accumulation_probe. Repository: /Users/richietate/Desktop/FeralEcho.

## Independent finding checkpoint (recorded before dedicated reviewer reports)

Checkpoint: 2026-09-22 12:23:46 UTC. This block records the independent reconstruction and provisional conclusions before opening the dedicated skeptic review, machine summary reports, hand-adjudication record, or research/reviewer narrative records. It is preserved in the final report rather than retrospectively rewritten.

Independence limitation: the initial primary-document batch included the Stage 1 draft. That protocol unexpectedly embeds Stage 0 interpretations and another claims ladder. Those passages were exposed before this checkpoint. Therefore this was a primary-evidence-first independent reconstruction, **not a fully blinded review with perfect compliance with the requested claims-ladder ordering**. Dedicated reviewer reports were deferred. Subsequent conclusions below come from independently inspected source, request/response ledgers, freezes, and fresh calculations; agreement with embedded prose was not treated as evidence.

**Provisional verdict:** the records support carrier-conditioned execution and a limited K1 example-to-table pathway. They do not establish accumulated competence, autonomous learning, foundation-model learning, or a qualified general acquisition pipeline. Stage 1 is not ready. A fixed compiler/serializer remains a sufficient alternative explanation for a future positive result. A non-learning doppelgänger survives under the mission's reasonable distinction between fixed prompt compilation and meaningful capability learning.

Independent numerical reconstruction at this checkpoint:

- Stage 0: all 554 planned response records present, no duplicate call IDs; eight intentional repeat probes match their originals. All request derivations, response digests, seed derivations, and ledger links checked.
- Original freeze: 32 artifact hashes and 14 source hashes match; qualification freeze: four artifact hashes and 23 source hashes match. Both protocol hashes match. QB's request/code/auditor hashes and qualification-freeze link match.
- Primary T/S scores: H 44/54; H2 45/54; N, N2, NEUTRAL, MISMATCH each 0/54; E 15/54; IC 12/54. H by K1/K2/K3 = 18/18, 11/18, 15/18. E = 13/18, 2/18, 0/18; IC = 12/18, 0/18, 0/18.
- Independently executed 1,010 stored worker programs in a disposable, restricted in-memory evaluator: 554 Stage 0, 432 QA gate, 24 QB gate. No repository module import, grader entry point, model call, or file write was used. Stage 0 agrees on 554/554 binary grades.
- Independently checked expected answers for all 280 Stage 0 and 240 qualification cases: no discrepancies.
- QA main drafts, independently read: K1 exact 6/6 R0, 5/6 R1; K2 and K3 0/6 in each representation. All 11 exact K1 main drafts pass the behavioral gate.
- GOLD gate: 10/12, below the frozen 0.85 threshold. K1 4/4, K2 2/4, K3 4/4. Both K2 world-1 replicates fail all four tasks by reversing priority in generated code. WRONG and NONE each 0/12.
- QB: 12 drafts, six empty responses, all six length-terminated at 3,000 tokens. K2 has five nonempty drafts, K3 one. Only those six drafts receive gate calls (24 total); none passes. No acquisition capability conclusion is justified from K3's five empty generations.
- K2's observed pairwise comparisons uniquely order the four known tags under the learner-supplied ranking schema. K1 identifies the six observed status mappings under its declared schema.
- K3 is not uniquely specified by the learner-visible task: the operation language used by the diagnostic is absent from the constructor prompt. For each observed event, both f(x) and f(x)+(x-2)(x-5)(x+1) fit all R0/R1 observations and can disagree materially elsewhere.
- The symbolic solver's narrow-family enumeration is useful conditional arithmetic, not independent evidence that the original LLM prompt supplied that family. Independently found defects include a K2 prefix-name tie-break error, K3 out-of-space explanations depending on sample order, and failure to classify impossible winner labels without an exception.
- Source-level grader bypass: a generated function can obtain answers from the global _CASES in its own execution module. No recorded response examined uses that route. This invalidates a claim of adversarial oracle isolation, not the independently reproduced historical grades.
- The generation jail restricts the experiment subtree, not all external reads or network endpoints. Trusted request assembly, rather than a complete confidentiality boundary, is what keeps observed prompts restricted.
- Prospective concerns: survivor-only primary pooling after acquisition failure; P-X uses disjoint token vocabularies; the gate lacks a control that rules out fixed compilation; no Stage 1 orchestrator or sealed Stage 1 directory was found.

Independent claims ladder at checkpoint:

| Claim | Classification | Boundary |
|---|---|---|
| Carrier consumption and behavioral consequence | ESTABLISHED | Conditional on these tasks, worlds, prompts, worker and scorer |
| K1 episode-to-procedure construction | SUPPORTED WITH BOUNDARIES | Known-code transcription; no experience-swap intervention yet |
| Experience dependence | SUPPORTED WITH BOUNDARIES | Correct content in episode-derived K1 drafts; direct causal experience intervention untested |
| K2 LLM induction | NOT ESTABLISHED | Tested constructors fail to state the available priority relation |
| K3 LLM induction | NOT ESTABLISHED | Both missing schema and concrete incorrect or absent outputs |
| Storage/reloading of draft text | ESTABLISHED | Qualification orchestration and ledgers |
| Retention by a qualified selection rule | NOT ESTABLISHED | Pooled GOLD sensitivity fails |
| Fresh-process acquired competence | NOT ESTABLISHED | Separate generation subprocess design exists; complete proposed boundary not exercised |
| Structural use of supplied conventions | SUPPORTED WITH BOUNDARIES | H on S = 12/18; this is instruction use, not learned transfer |
| Experience-derived sealed transfer/generalization | UNTESTED | Stage 1 not run |
| Accumulated competence / autonomous learning | UNTESTED | No accumulation or autonomous evidence selection |
| Foundation-model learning | NOT ESTABLISHED | No weight update or relevant intervention |
| FeralEcho-system acquisition | NOT ESTABLISHED | Production memory/council/learning paths are not exercised |
| Self-improvement | UNTESTED | No evaluated improving system |

The simplest surviving account is: a frozen model follows supplied instructions; K1 observations can be transcribed into instructions; K2 induction and execution are separately unreliable; K3 asks for extrapolation without stating the evaluator's restricted rule family. A future fixed compiler could produce experience-specific persistent instructions and satisfy the behavioral gates without acquiring a new learning mechanism.

The completed report and reviewer comparison follow below.
~~~~

</details>

## Appendix B. Before/after integrity record

Baseline file fingerprint: **2026-09-22T12:15:31.388212+00:00**. Post-investigation measurement after resumption: **2026-09-22T17:13:30.999480+00:00**. A further check after full report assembly at **2026-09-22T17:17:18.178621+00:00** confirmed the same HEAD, unchanged 162-file fingerprints, no new AP-0 files, and the sole Git-status addition shown below. All source links and all 22 numbered report sections were verified. Recording this final-check sentence changes only this report.

| Measurement | Before | After |
|---|---|---|
| HEAD | 2fba42644c82b9f7096276f4dd338d615cf1bcce | Same |
| Branch/upstream | main / origin/main, +17 −0 | Same |
| Modified tracked paths | 27 | 27, identical status records |
| Staged paths | 0 | 0 |
| Untracked paths | 262 | 263 |
| Added status record | — | ? audits/2026-09-22_codex_ap0_independent_forensic_audit.md |
| Other status differences | — | None |
| Pre-existing fingerprinted files | 162; 24,477,086 bytes | Same bytes, SHA-256 and permissions for every file |
| New AP-0 source/artifact files | — | None |
| Deleted fingerprinted files | — | None |

Git-state file SHA-256 values, identical before/after:

~~~text
.git/index           0a71527c568dd6f19052d4bcaf084db79df8928e1ff83bb75b546af0b5a1bf08
.git/HEAD            28d25bf82af4c0e2b72f50959b2beb859e3e60b9630a5e8c603dad4ddb2b6e80
.git/refs/heads/main e5d5403269897b8b11fcf73f96897f9e6eb86635f9ca0e10412ad90f29644f4d
~~~

Exact porcelain-v2 output hashes (UTF-8, including trailing newline):

~~~text
before f0f1951f1c5801fb3f175110c6486227f413e080e2b22107ccc699d8135655d9
after  f962ba7ef0f19eddc8781d9bd96543365783a79c5e0702f64dfdd96e8ca915f4
~~~

The canonical fingerprint-map hash is **6c711a325286cebf35a31843a8ab46b79d8637783a27da6e0adda611b389e65c**. Its input is the map from relative path to {sha256, size, mode}, serialized as Python json.dumps(map, sort_keys=True, separators=(',', ':'), ensure_ascii=True). The full initial map is recorded below. This is an audit measurement, not an independent external timestamp/signature.

No change was observed in captured modification-time fields either. I did not monitor every runtime memory page, cache, log, access-time update or unrelated background file on the host, and do not claim such an attestation. The meaningful guarantees here are the measured evidence/Git content invariants and the absence of audit actions invoking model/runtime mutations.

### Verified ledger endpoints and response duplication

These are stored-response hash chains, not complete network-attempt logs. Distinct content counts are within each ledger; repeated text across separate calls is expected and is different from duplicate call IDs.

| Ledger under memory/experiments/accumulation_probe | Rows | Distinct response hashes | Verified final chain hash |
|---|---:|---:|---|
| stage0/runs/E/calls.jsonl | 54 | 38 | 131d6e3aef547626fd1d2b9334bf61f169510f303cbe889579e37959635e05c8 |
| stage0/runs/H/calls.jsonl | 112 | 58 | b2100a488969258f4146e865f83946a6963e73f0178c62994d294bed658685cf |
| stage0/runs/H2/calls.jsonl | 54 | 34 | 252dfc510e60bf5ce8bf8e71499572b660b3379234ebd8aefebff6930a5a0c71 |
| stage0/runs/IC/calls.jsonl | 54 | 34 | dc1050e1b10259d60c02066728efc180a3e25c38583d95953183a4330b2af16a |
| stage0/runs/MISMATCH/calls.jsonl | 54 | 40 | 877fee84d2a94e27663d6b8ee80f895f9a484edfff2530403db1973fb439e336 |
| stage0/runs/N/calls.jsonl | 88 | 55 | d71cb9c019a0430e18202976b2f7392a5e6450a4412b41f2af6b9abd1df10a2d |
| stage0/runs/N2/calls.jsonl | 54 | 32 | f4f3f51b7a8e37422f20f1413c8e08cc13596d0c9051161b81af08cad961271a |
| stage0/runs/NEUTRAL/calls.jsonl | 84 | 60 | 012f6a8aad387256faf28fe340df16024de41572d08b28d409da8c6997101299 |
| v2/qual/roots/construct/calls.jsonl | 72 | 72 | 4c124798ed02c1803b03c0ef55406f8d69e97f99943398f92008a23f53e9eeb8 |
| v2/qual/roots/gate/calls.jsonl | 432 | 359 | bc5df21531571c679064b5039dda3c8c3a6217f6c2df0e57fcd8d1283b092ad0 |
| v2/qual/roots/qb_construct/calls.jsonl | 12 | 7 | de4d17e90ce8e884f61d8094ed36e85940d606fe186b03b2fb933893b373a4ea |
| v2/qual/roots/qb_gate/calls.jsonl | 24 | 21 | 3667d5e6e09a0f990812ec8ce5c9dd7fb74b1f13f556369553858036a28b5e68 |

<details>
<summary>Complete initial Git status; final status adds only the report path stated above</summary>

~~~text
# branch.oid 2fba42644c82b9f7096276f4dd338d615cf1bcce
# branch.head main
# branch.upstream origin/main
# branch.ab +17 -0
1 .M N... 100644 100644 100644 2cfa5adbd10260f14bfac5fd3ba750c9679a25ab 2cfa5adbd10260f14bfac5fd3ba750c9679a25ab CLAUDE.md
1 .M N... 100644 100644 100644 a77e3c134691758cfdfe0b9321147597ff53a80f a77e3c134691758cfdfe0b9321147597ff53a80f PENDING_DECISIONS.md
1 .M N... 100644 100644 100644 b284719f3d3afb3feb4a3fc9c76f3349b36ec4ad b284719f3d3afb3feb4a3fc9c76f3349b36ec4ad app/core/echo_ground_truth.py
1 .M N... 100644 100644 100644 28bcabc9dee8654385d28fbc6cbde3b526ac5949 28bcabc9dee8654385d28fbc6cbde3b526ac5949 app/core/liveness_ledger.py
1 .M N... 100644 100644 100644 d4cb1efa5d78670d857ec202e5a951a828fbfa1f d4cb1efa5d78670d857ec202e5a951a828fbfa1f app/core/provenance_check.py
1 .M N... 100644 100644 100644 d1fc1480b8c17b4a350364d05588e91681fcbba8 d1fc1480b8c17b4a350364d05588e91681fcbba8 app/core/river_deliberation.py
1 .M N... 100644 100644 100644 c67116298080f263d430adb8b0bda3a347b366ce c67116298080f263d430adb8b0bda3a347b366ce app/core/self_edit_convergence.json
1 .M N... 100644 100644 100644 4988ab4df583d9c9ea45848fb11ec82bfe7368a1 4988ab4df583d9c9ea45848fb11ec82bfe7368a1 app/core/self_edit_generated.py
1 .M N... 100644 100644 100644 d5037b67298b3a99ccfbec710a43fac1c4d4954e d5037b67298b3a99ccfbec710a43fac1c4d4954e app/core/self_edit_manager.py
1 .M N... 100644 100644 100644 c99090b37eda4a2e9c9a4bcc05169b60fea36979 c99090b37eda4a2e9c9a4bcc05169b60fea36979 app/core/shadow_model.py
1 .M N... 100644 100644 100644 bc6dd0e3f4ca06f026632a72feafacbc79fcebb0 bc6dd0e3f4ca06f026632a72feafacbc79fcebb0 app/core/snapshot_manager.py
1 .M N... 100644 100644 100644 b35bc8c291f7bf4be289ee05cae27108da8665eb b35bc8c291f7bf4be289ee05cae27108da8665eb app/core/temporal_environment.py
1 .M N... 100644 100644 100644 002b70c8932be5ae1830fcb8abe06a7a5a516724 002b70c8932be5ae1830fcb8abe06a7a5a516724 app/emergent_scheduler.py
1 .M N... 100644 100644 100644 1fdc6f43a92991364b1cf6262c44761b6b8018b1 1fdc6f43a92991364b1cf6262c44761b6b8018b1 app/maintenance/night_cycle.py
1 .M N... 100644 100644 100644 b3e1a6b0250af03c88d67e22f7df4da09254d4a7 b3e1a6b0250af03c88d67e22f7df4da09254d4a7 audits/2026-09-14_tier5_followup_experiment_design.md
1 .M N... 100644 100644 100644 edce4d8e9ed97d0fd7551ce9297e2e4487a58d04 edce4d8e9ed97d0fd7551ce9297e2e4487a58d04 claude_relay/.last_seen_from_air.json
1 .M N... 100644 100644 100644 b7d1e5b36c04a3bc0f2cc07fb34d38e2fa2bc561 b7d1e5b36c04a3bc0f2cc07fb34d38e2fa2bc561 claude_relay/README.md
1 .M N... 100644 100644 100644 94d25ca86ca2cfcdcb14c7fcfde4f17e99472e27 94d25ca86ca2cfcdcb14c7fcfde4f17e99472e27 claude_relay/from_m5.md
1 .M N... 100644 100644 100644 3256a14243cf211ab0c215022d7e16f949f17823 3256a14243cf211ab0c215022d7e16f949f17823 claude_relay/relay.py
1 .M N... 100644 100644 100644 3ac055d93b4f37427939b8717d6ecbb8bb5a3c54 3ac055d93b4f37427939b8717d6ecbb8bb5a3c54 logs/janitor_report.json
1 .M N... 100644 100644 100644 baa3d70a856a9ac69aa56df572cd55e0334a0876 baa3d70a856a9ac69aa56df572cd55e0334a0876 research/OPEN_QUESTIONS.md
1 .M N... 100755 100755 100755 7fc8bbc69b93b27bd8aa3aaeb69441f01a48e2e2 7fc8bbc69b93b27bd8aa3aaeb69441f01a48e2e2 run.py
1 .M N... 100644 100644 100644 63464ad18563b9a22b14ddbc8b9f0f61e500dcca 63464ad18563b9a22b14ddbc8b9f0f61e500dcca sandbox/safe_exec_wrapper.py
1 .M N... 100644 100644 100644 77c46e65f865a6193da1ded49aa27e30770a34f1 77c46e65f865a6193da1ded49aa27e30770a34f1 sandbox/scripts/temp_self_edit.py
1 .M N... 100644 100644 100644 ed3d174d86c03f68372bd9a4e97ae6a2ed3f0668 ed3d174d86c03f68372bd9a4e97ae6a2ed3f0668 scripts/verify_liveness_ledger.py
1 .M N... 100644 100644 100644 87d82c6818cf48ec1cfe5d1ddc992f8491ae0ec5 87d82c6818cf48ec1cfe5d1ddc992f8491ae0ec5 scripts/verify_provenance_check.py
1 .M N... 100644 100644 100644 9b125fe5c456bc70d95252e949b06d924695c1d5 9b125fe5c456bc70d95252e949b06d924695c1d5 staging/self_edit_candidate.py
? .claude/plans/verified-humming-otter.md
? .claude/settings.json
? .claude/skills/README.md
? .claude/skills/feral-forensic-audit/SKILL.md
? .claude/skills/feral-forensic-audit/references/adversarial-checklist.md
? .claude/skills/feral-forensic-audit/references/evidence-ledger-schema.md
? .claude/skills/feral-forensic-audit/references/evidence-vocabulary.md
? .claude/skills/feral-forensic-audit/references/integrity-and-safety.md
? .claude/skills/feral-forensic-audit/references/report-template.md
? .claude/skills/feral-independent-review/SKILL.md
? .claude/skills/feral-independent-review/references/reviewer-checklist.md
? app/experiments/accumulation_probe/__init__.py
? app/experiments/accumulation_probe/audit_v2.py
? app/experiments/accumulation_probe/build_stage0.py
? app/experiments/accumulation_probe/common.py
? app/experiments/accumulation_probe/constructor.py
? app/experiments/accumulation_probe/dev_analyze.py
? app/experiments/accumulation_probe/dev_run.py
? app/experiments/accumulation_probe/freeze.py
? app/experiments/accumulation_probe/grade.py
? app/experiments/accumulation_probe/jail.py
? app/experiments/accumulation_probe/ollama_client.py
? app/experiments/accumulation_probe/oracle_b.py
? app/experiments/accumulation_probe/oracle_b_v2.py
? app/experiments/accumulation_probe/oracle_runner.py
? app/experiments/accumulation_probe/prompts.py
? app/experiments/accumulation_probe/qb.py
? app/experiments/accumulation_probe/qual.py
? app/experiments/accumulation_probe/qual_ident.py
? app/experiments/accumulation_probe/qual_posthoc.py
? app/experiments/accumulation_probe/reaudit_stage0.py
? app/experiments/accumulation_probe/run_arm.py
? app/experiments/accumulation_probe/run_gen.py
? app/experiments/accumulation_probe/stage0.py
? app/experiments/accumulation_probe/tasks.py
? app/experiments/accumulation_probe/tasks_v2.py
? app/experiments/accumulation_probe/val_select.py
? app/experiments/accumulation_probe/worlds.py
? app/experiments/e5_mini/__init__.py
? app/experiments/e5_mini/accounting.py
? app/experiments/e5_mini/applicability.py
? app/experiments/e5_mini/builder.py
? app/experiments/e5_mini/checker.py
? app/experiments/e5_mini/ledger.py
? app/experiments/e5_mini/manifests/__init__.py
? app/experiments/e5_mini/manifests/example_synthetic.py
? app/experiments/e5_mini/manifests/resource_budget_manifest.py
? app/experiments/e5_mini/manifests/role_access_manifest.py
? app/experiments/e5_mini/manifests/task_manifest.py
? app/experiments/e5_mini/mock.py
? app/experiments/e5_mini/oracle.py
? app/experiments/e5_mini/orchestrator.py
? app/experiments/e5_mini/sandbox.py
? app/experiments/e5_mini/schema.py
? app/experiments/e5_mini/tests/__init__.py
? app/experiments/e5_mini/tests/test_e5_mini_g0.py
? app/experiments/e5_mini/tests/test_manifests.py
? app/experiments/real_trace_f2_provenance/_scratch/river_brain_scratch.pkl
? app/experiments/real_trace_f2_provenance/_scratch/river_brain_scratch.pkl.lock
? app/experiments/task_type_ground_truth/__init__.py
? app/experiments/task_type_ground_truth/blind_label.py
? app/experiments/task_type_ground_truth/dataset.py
? app/experiments/task_type_ground_truth/evaluate.py
? app/experiments/task_type_ground_truth/gold_labels.jsonl
? app/experiments/task_type_ground_truth/gold_labels_llm.jsonl
? app/experiments/task_type_ground_truth/schema.py
? audits/2026-09-07_authority_boundary_deliberateness.md
? audits/2026-09-07_consequence_authority_map.md
? audits/2026-09-07_consequential_learning_loop_design.md
? audits/2026-09-07_consequential_loop_validation.md
? audits/2026-09-07_missing_primitive_determination.md
? audits/2026-09-07_post_wake_observation.md
? audits/2026-09-07_shadow_treatment_harness_archaeology.md
? audits/2026-09-07_temporal_authority_graph.md
? audits/2026-09-08_adversarial_epistemic_pressure.md
? audits/2026-09-08_echo_blind_self_model.md
? audits/2026-09-08_echo_self_model_claims.json
? audits/2026-09-08_echo_self_model_discrepancy_report.md
? audits/2026-09-08_echo_self_model_revision.md
? audits/2026-09-08_epistemic_arbitration_FINAL.md
? audits/2026-09-08_epistemic_arbitration_baseline.md
? audits/2026-09-08_epistemic_arbitration_design.md
? audits/2026-09-08_epistemic_arbitration_experiments.md
? audits/2026-09-08_epistemic_arbitration_pipeline.md
? audits/2026-09-08_epistemic_arbitration_validation.md
? audits/2026-09-08_epistemic_boundary_imagination_experiment.md
? audits/2026-09-08_epistemic_contamination_recovery_forensics.md
? audits/2026-09-08_epistemic_interaction_and_relay_forensics.md
? audits/2026-09-08_epistemic_transition_mechanism_forensics.md
? audits/2026-09-08_evidence_arbitration_and_sensory_ingestion_forensics.md
? audits/2026-09-08_exhaustive_sensor_contract_experiment.md
? audits/2026-09-08_git_readonly_self_history_investigation.md
? audits/2026-09-08_mechanism_c_FINAL.md
? audits/2026-09-08_mechanism_c_experiments.md
? audits/2026-09-08_mechanism_c_post_update_replication.md
? audits/2026-09-08_mechanism_d_independent_regrounding.md
? audits/2026-09-08_persistent_self_model_DESIGN.md
? audits/2026-09-08_persistent_self_model_inventory.md
? audits/2026-09-08_phase10_retest_after_revision.md
? audits/2026-09-08_phase8_adversarial_testing.md
? audits/2026-09-08_self_model_causal_design.md
? audits/2026-09-08_self_model_contradiction_handling.md
? audits/2026-09-08_self_model_correction_path.md
? audits/2026-09-08_self_model_evidence_hierarchy.md
? audits/2026-09-08_self_model_experiment_plan.md
? audits/2026-09-08_self_transparency_audit_FINAL.md
? audits/2026-09-08_self_transparency_audit_experimental_boundary.md
? audits/2026-09-08_sensory_gate_fix_and_provenance_forensics.md
? audits/2026-09-08_transparency_metrics_and_epistemic_boundary.md
? audits/2026-09-08_verified_external_architecture.md
? audits/2026-09-09_autonomous_investigation_liveness_recovery_forensics.md
? audits/2026-09-09_autonomous_scheduler_restart_temporal_lifecycle_forensics.md
? audits/2026-09-09_codex_headless_subscription_independence_proof.md
? audits/2026-09-09_epistemic_transition_mechanism_forensics.md
? audits/2026-09-09_four_agent_collaboration_architecture_audit.md
? audits/2026-09-09_independent_review_epistemic_arbitration_findings.md
? audits/2026-09-09_mission32_task_type_classifier_causal_audit.md
? audits/2026-09-09_mission32_task_type_classifier_causal_audit_evidence_ledger.json
? audits/2026-09-09_mission33_independent_ground_truth_audit.md
? audits/2026-09-09_mission34_task_type_experiment_run.md
? audits/2026-09-09_mission35_task_type_experiment_llm_judge_rerun.md
? audits/2026-09-09_open_ended_learning_discovery.md
? audits/2026-09-09_openai_codex_local_agent_architecture_investigation.md
? audits/2026-09-09_os_level_stdin_fd0_implementation.md
? audits/2026-09-10_epistemic_invocation_and_provenance_isolation.md
? audits/2026-09-10_phase2_provenance_reconciliation.md
? audits/2026-09-10_research_arc_provenance_audit.md
? audits/2026-09-11_authority_evidence_separation_forensics.md
? audits/2026-09-11_authority_free_ladder_causal_isolation.md
? audits/2026-09-11_false_verification_trap_replication.md
? audits/2026-09-11_feralecho_unresolved_defect_audit.md
? audits/2026-09-11_provenance_implementation_boundary_audit.md
? audits/2026-09-11_provenance_leaf_primitives_validation.md
? audits/2026-09-11_read_only_git_provenance_design.md
? audits/2026-09-11_read_only_provenance_interface_design.md
? audits/2026-09-11_research_state_consolidation.md
? audits/2026-09-11_three_layer_provenance_reconciliation.md
? audits/2026-09-11_verification_and_level_7_5_8_feasibility.md
? audits/2026-09-12_provenance_layer2_boundary_review.md
? audits/2026-09-13_capability_benchmark_harness_phase0.md
? audits/2026-09-13_council_correctness_investigation.md
? audits/2026-09-13_cross_layer_reconciliation_boundary.md
? audits/2026-09-13_layer3_runtime_provenance_boundary.md
? audits/2026-09-13_observation_time_contract_research.md
? audits/2026-09-13_observation_time_enforcement_research.md
? audits/2026-09-13_observation_time_placement_architecture.md
? audits/2026-09-13_provenance_layer2_red_team.md
? audits/2026-09-13_reconciliation_epistemic_taxonomy_and_arbitration_scoping.md
? audits/2026-09-13_reconciliation_implementation.md
? audits/2026-09-13_reconciliation_implementation_design.md
? audits/2026-09-13_reconciliation_primitive_architecture.md
? audits/2026-09-13_shadow_model_retirement.md
? audits/2026-09-13_shadow_retirement_documentation.md
? audits/2026-09-13_tier5_council_correctness_retest.md
? audits/2026-09-14_core_task_misclassification_council_synthesis_trace.md
? audits/2026-09-14_task_type_behavioral_experiment.md
? audits/2026-09-14_task_type_downstream_behavior_archaeology.md
? audits/2026-09-14_tier5_retest_adversarial_audit.md
? audits/2026-09-15_codex_michelangelo_blind_spot_discovery.md
? audits/2026-09-15_codex_task_type_independent_review.md
? audits/2026-09-15_task_type_experiment_reconciliation.md
? audits/2026-09-16_capability_growth_reconciliation.md
? audits/2026-09-16_codex_capability_ceiling_adversarial_review.md
? audits/2026-09-16_e5_mini_adversarial_preimplementation_review.md
? audits/2026-09-16_e5_mini_codex_reconciliation.md
? audits/2026-09-16_e5_mini_codex_requalification_reconciliation.md
? audits/2026-09-16_e5_mini_final_adjudication.md
? audits/2026-09-16_e5_mini_g0_codex_adversarial_review.md
? audits/2026-09-16_e5_mini_g0_codex_requalification_attack.md
? audits/2026-09-16_e5_mini_g0_mock_implementation.md
? audits/2026-09-16_e5_mini_g0_repair_and_requalification.md
? audits/2026-09-16_e5_mini_manifests_design_and_hostile_review.md
? audits/2026-09-16_feralecho_zero_cost_capability_ceiling.md
? audits/2026-09-17_learning_signal_evaluator_qualification.md
? audits/2026-09-17_python_env_inventory_raw.txt
? audits/2026-09-17_python_learning_capability_gap_audit.md
? audits/2026-09-17_recursive_learning_ground_truth_investigation.md
? audits/2026-09-17_task_type_map_sync_ground_truth_and_qualification.md
? audits/2026-09-19_persistent_competence_candidate_tournament.md
? audits/2026-09-19_persistent_competence_experiment_adversarial_review.md
? audits/2026-09-19_persistent_competence_experiment_design.md
? audits/2026-09-19_persistent_competence_experiment_design_evidence_ledger.json
? audits/2026-09-20_feralecho_architectural_integrity_audit.md
? audits/2026-09-20_feralecho_architecture_evidence_ledger.json
? audits/2026-09-20_feralecho_backup_manifest_schema.json
? audits/2026-09-20_feralecho_cross_backup_relay_schema.json
? audits/2026-09-20_feralecho_m5_intel_cross_backup_relay_plan.md
? audits/2026-09-20_feralecho_runtime_identity_and_state_preservation.md
? audits/2026-09-20_feralecho_runtime_identity_manifest.json
? audits/2026-09-20_feralecho_state_preservation_evidence.json
? audits/2026-09-20_feralecho_verified_backup_and_recovery_plan.md
? audits/2026-09-20_persistent_competence_frozen_protocol.json
? audits/2026-09-20_persistent_competence_frozen_protocol.md
? audits/2026-09-20_persistent_competence_frozen_protocol_v1_1.json
? audits/2026-09-20_persistent_competence_frozen_protocol_v1_1.md
? audits/2026-09-20_persistent_competence_protocol_v1_blind_review.md
? audits/2026-09-20_persistent_competence_v1_to_v1_1_traceability.md
? audits/2026-09-20_seagate_2tb_echo_vault_preflight.md
? audits/2026-09-20_seagate_apfs_encrypted_format_preflight.md
? audits/2026-09-21_ap0_stage0_preregistration_v1.md
? audits/2026-09-21_ap0_stage1_preregistration_v2_DRAFT.md
? audits/2026-09-21_ap0_v2_causal_chain_and_skeptic_review.md
? audits/2026-09-21_ap0_v2_constructor_qualification_protocol.md
? audits/2026-09-21_seagate_post_f1_guard_diagnostic.md
? audits/python_learning_capability_gap/dependency_metadata_check.json
? audits/python_learning_capability_gap/environment_inventory.json
? audits/python_learning_capability_gap/installed_capability_probes.json
? audits/python_learning_capability_gap/inventory.py
? audits/python_learning_capability_gap/probes.py
? audits/python_learning_capability_gap/runtime_identity.json
? audits/python_learning_capability_gap/source_import_inventory.json
? audits/python_learning_capability_gap/upstream_research.json
? audits/recursive_learning_ground_truth/accumulation.py
? audits/recursive_learning_ground_truth/archived_output_probe.py
? audits/recursive_learning_ground_truth/followup.py
? audits/recursive_learning_ground_truth/probe.py
? audits/recursive_learning_ground_truth/r1_r3_results.json
? audits/recursive_learning_ground_truth/r4_consumer.json
? audits/recursive_learning_ground_truth/r4_producer.json
? audits/recursive_learning_ground_truth/r5_memory.json
? audits/recursive_learning_ground_truth/r6_t0.json
? audits/recursive_learning_ground_truth/r6_t1.json
? audits/recursive_learning_ground_truth/r6_t2.json
? audits/recursive_learning_ground_truth/r6_t3.json
? audits/recursive_learning_ground_truth/r8_shortcut.json
? audits/recursive_learning_ground_truth/r9_archived_outputs.json
? audits/tier3_apparatus/dev_sanity_results_REISOLATED_RERUN_20260909.jsonl
? audits/tier3_apparatus/heldout_results_REISOLATED_RERUN_20260909.jsonl
? audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_progress.txt
? audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_results.jsonl
? audits/tier5_retest/tier5_retest_progress.txt
? audits/tier5_retest/tier5_retest_results.jsonl
? audits/tier5_retest/tier5_retest_task_pool.hash.txt
? audits/tier5_retest/tier5_retest_task_pool_FROZEN.py
? claude_relay/.last_seen_from_air_hub.json
? claude_relay/facts_m5.jsonl
? codex_relay/README.md
? codex_relay/relay.py
? codex_relay/test_relay.py
? hub/README.md
? hub/check_hub.py
? hub/notes.jsonl
? hub/notes.py
? hub/status.jsonl
? research/COLLABORATOR_SUBSTITUTION_CODEX_PILOT.md
? research/FRONTIER_COLLABORATOR_REGULATORY_DEPENDENCY.md
? research/MACOS_AUTHORIZATION_EVIDENCE_ARCHEOLOGY.md
? research/MEMORY_PRESERVATION_ARCHAEOLOGY.md
? research/MEMORY_PRESERVATION_SET_AUDIT.md
? research/OPOSSUM_MODE_BRAINSTORM.md
? research/STRATEGIC_FRONTIER_RESILIENCE.md
? research/TWO_NODE_IDENTITY_PRESERVATION_RELAY_ARCHAEOLOGY.md
? scripts/run_tier3_reisolated_rerun.py
? scripts/run_tier5_retest.py
? scripts/task_type_behavioral_experiment.py
? scripts/task_type_behavioral_experiment_analyze.py
? scripts/task_type_behavioral_experiment_judge.py
? scripts/tier5_retest_task_pool.py
? scripts/verify_accumulation_probe.py
? scripts/verify_accumulation_probe_v2.py
? scripts/verify_qual_ident.py
? scripts/verify_select_best_fallback_candidate.py
~~~

</details>

<details>
<summary>Complete 162-file baseline content fingerprint, unchanged afterward</summary>

| Relative path | Bytes | Mode | SHA-256 |
|---|---:|---|---|
| .git/HEAD | 21 | 0o644 | 28d25bf82af4c0e2b72f50959b2beb859e3e60b9630a5e8c603dad4ddb2b6e80 |
| .git/index | 88072 | 0o644 | 0a71527c568dd6f19052d4bcaf084db79df8928e1ff83bb75b546af0b5a1bf08 |
| .git/refs/heads/main | 41 | 0o644 | e5d5403269897b8b11fcf73f96897f9e6eb86635f9ca0e10412ad90f29644f4d |
| CLAUDE.md | 558122 | 0o644 | 4c3f78706c7c40f41ab025eb63470813944b575c9ae02b8afe00c422729a8556 |
| PENDING_DECISIONS.md | 17210 | 0o644 | c18b31b48ed21de3a9144391f80c54a8383b7f89c0ab93751ba528528167b8c6 |
| app/core/echo_ground_truth.py | 58572 | 0o644 | 9b78bd9ed91c61da72dddcba543979bc5ba717ddd2b04ef75d57e5a648979005 |
| app/core/liveness_ledger.py | 195641 | 0o644 | e714ec96a3dcfe8782df51a5d06891657aed0988976e2fc89a02deb9111f2db8 |
| app/core/provenance_check.py | 65983 | 0o644 | c863288235dcff3e5f4b56bc956ccb81447ac52c74fa3d2a456d097784715acb |
| app/core/river_deliberation.py | 79741 | 0o644 | 5d1aa77911509ebbc90d01cd084e5ac3b4c8bd7b9790bc2780b5ce226c253585 |
| app/core/self_edit_convergence.json | 4692 | 0o644 | ddba8fc31e797579a44fb8470e96ba5d351e29f05e064c3dd733610af398004b |
| app/core/self_edit_generated.py | 922 | 0o644 | 9616e89a114ff3026c265681809682e6c5621fd2402f034d8c346d589dbce4c2 |
| app/core/self_edit_manager.py | 141706 | 0o644 | 2e747acc5bf353335596ddc75c94025dc51e7866cef6127aa1042fa9a1a0b36a |
| app/core/shadow_model.py | 9159 | 0o644 | ca5940c89e9db59bad700a7a18107737dcf2c4e04ab553934a184fb91bb5e949 |
| app/core/snapshot_manager.py | 38052 | 0o644 | 95f5a0cf1b62a4a21fe608cb26f7febceb08793e1640adab591ff85b8a95e1a1 |
| app/core/temporal_environment.py | 9954 | 0o666 | 4dcad97f2d2f526b75033d89fcb91813b0a50b3f92a0c222e89d63d87c0b9ccd |
| app/emergent_scheduler.py | 49450 | 0o666 | 1ea77319bb8647c17fea40ac9025d44111ed700b89ae8cffc69a1ee4c3b2fe0d |
| app/experiments/accumulation_probe/__init__.py | 626 | 0o644 | bf7755cb493f3f17618909ff8dc3b314dc68e3dd84321d1e882e50d1c6b437fa |
| app/experiments/accumulation_probe/__pycache__/__init__.cpython-312.pyc | 818 | 0o644 | 812d2ed90fd293478b71108edf34cb5f09a97126bf918157cdc2b339b3cd8bfa |
| app/experiments/accumulation_probe/__pycache__/audit_v2.cpython-312.pyc | 4680 | 0o644 | f1539c307b5f15d3a75e6f19f5fd1b08b20ab7f81529c23a48b51753fbf3e4ad |
| app/experiments/accumulation_probe/__pycache__/common.cpython-312.pyc | 4695 | 0o644 | 6bd1bb2862f8a63815b3412de04529e38e72ea8130f911ccddc8bfed58b81e93 |
| app/experiments/accumulation_probe/__pycache__/constructor.cpython-312.pyc | 12067 | 0o644 | 4b50e43461c2a9e6909f5935b2dd26b364c221cd433948d0d55c3090b26bc167 |
| app/experiments/accumulation_probe/__pycache__/freeze.cpython-312.pyc | 9337 | 0o644 | e915356cf6de5df435115c6689f7910e1a83de8dc4bd12e462114faa4d1b2b6a |
| app/experiments/accumulation_probe/__pycache__/jail.cpython-312.pyc | 1619 | 0o644 | f288e9a2980b3791e476d104962a56978b73910607411835cbe4e8103c105b19 |
| app/experiments/accumulation_probe/__pycache__/ollama_client.cpython-312.pyc | 2729 | 0o644 | 9e11fa00d31266061c21cbf6b1f3c64221fac125efe7b072cfb178645c2d0285 |
| app/experiments/accumulation_probe/__pycache__/oracle_b.cpython-312.pyc | 11071 | 0o644 | 2da875ba9b278ba2987d74c301ff723e5acdc6d9b057294a158db85232b8cb41 |
| app/experiments/accumulation_probe/__pycache__/oracle_b_v2.cpython-312.pyc | 11616 | 0o644 | 687330dca11616ada5449d55ace8df4b18aaf1af4b01928b078ccb8815eaa0a1 |
| app/experiments/accumulation_probe/__pycache__/oracle_runner.cpython-312.pyc | 5461 | 0o644 | 3d91a87146b4ff56249eda4f1bd53288214cdae8a16642c053d85f156257a9e1 |
| app/experiments/accumulation_probe/__pycache__/prompts.cpython-312.pyc | 2567 | 0o644 | 5d5d09cd7b27a1b5c6bde44649c5cd694159e1ccc508ac4ec0448e2781aebb09 |
| app/experiments/accumulation_probe/__pycache__/qb.cpython-312.pyc | 12887 | 0o644 | b2e81ce94912bd0d30b0d87f814f43a04bb44afa61c2e94c2204aed2058c1f2e |
| app/experiments/accumulation_probe/__pycache__/qual.cpython-312.pyc | 33448 | 0o644 | 2eaec331f58cb35c9bd5bbf51af1e666f32fe524ca1a45f2f77173466eaabb03 |
| app/experiments/accumulation_probe/__pycache__/qual_ident.cpython-312.pyc | 10485 | 0o644 | 085893197472219971e6ca3826287ecd767a8e8db42a80e139d46f6adec4bda5 |
| app/experiments/accumulation_probe/__pycache__/tasks.cpython-312.pyc | 32997 | 0o644 | 8ca27846d884106e9a03b49fdf1b1b5a5fb9cd5cdbd49f258c56f87db8a247d4 |
| app/experiments/accumulation_probe/__pycache__/tasks_v2.cpython-312.pyc | 35733 | 0o644 | 348ea2d97e0a9bc9f76f67a4022458de001f5ba4c414d45c86ce9a1d92ac113d |
| app/experiments/accumulation_probe/__pycache__/worlds.cpython-312.pyc | 7667 | 0o644 | 5a681e5f2761ac6273c648c722b37b358840e0bc359163908d264a82c2acd13f |
| app/experiments/accumulation_probe/audit_v2.py | 2787 | 0o644 | bbec01e141fa997ded7d0f0af7faebd842be1ed18903bd7c02655d5c4197f3ee |
| app/experiments/accumulation_probe/build_stage0.py | 17555 | 0o644 | ece64e85c8b581d13995281b1402d3745710ab7a132dbd866e6a9f7ba0ac7ac0 |
| app/experiments/accumulation_probe/common.py | 2047 | 0o644 | 3956e780339722708108e96c4524d6d30415d7cafe108be8fd8a273501b0c03f |
| app/experiments/accumulation_probe/constructor.py | 6937 | 0o644 | e00c3dd8cb70804d11bd378b7438dd835fff911da0ab9aea677b6c824afa3538 |
| app/experiments/accumulation_probe/dev_analyze.py | 2859 | 0o644 | 3a9898b9f0737853845b1d53b31800d45f7f73825d1e4e1201b4bd16ba3df176 |
| app/experiments/accumulation_probe/dev_run.py | 2854 | 0o644 | 2ee9d46fc15a866f71e702089d314a1a3891be8b12e9293954804bad952a80fe |
| app/experiments/accumulation_probe/freeze.py | 4740 | 0o644 | ab86015a3ee8ac2407d5f84c63af0883f27950260bcc80bbf8d6465f5a453291 |
| app/experiments/accumulation_probe/grade.py | 17272 | 0o644 | e53fd1596661ee5837c813106866cbfa461bbea36c408aeceadc035f984a87fb |
| app/experiments/accumulation_probe/jail.py | 991 | 0o644 | 044f9d80379f7931de6e12d682540c92845f7901a3b056b3d35a8e4dc25a6501 |
| app/experiments/accumulation_probe/ollama_client.py | 1446 | 0o644 | dc4de03ac351d90510ef8c50e4cea695293de6b3b41a5f59b388ccedfab2c3dc |
| app/experiments/accumulation_probe/oracle_b.py | 3940 | 0o644 | 7cf9133008e630d19888a6ccf2544e6bf84b76f90a70ca37925ff1de36748e46 |
| app/experiments/accumulation_probe/oracle_b_v2.py | 3388 | 0o644 | fb59d5ec436b923e677f2dd14ff469764a11b941d84cfe6fda74937ffc3ff6aa |
| app/experiments/accumulation_probe/oracle_runner.py | 3389 | 0o644 | 12a6420959ce8a55222397e9bbba285c64242a90f4637302c3a2275dc1169c75 |
| app/experiments/accumulation_probe/prompts.py | 1641 | 0o644 | 2d1ef317382020752b5802c85ac9ae884eee567316bc609143b2746af57c476c |
| app/experiments/accumulation_probe/qb.py | 6079 | 0o644 | 13fcc469dc1b9fa28ac0a3f1b4218f9798ffef0860187b891337f2f9eb7f0089 |
| app/experiments/accumulation_probe/qual.py | 14817 | 0o644 | c7257ebc861b5dad93c22ff963eb6b59d4455e696214567a67dc5729a23d8683 |
| app/experiments/accumulation_probe/qual_ident.py | 7581 | 0o644 | f98a0d2056426209acf267a6b4c624e468301d529715b749e255121a6c66eecd |
| app/experiments/accumulation_probe/qual_posthoc.py | 641 | 0o644 | 8da4ba83acb258390345fd65d06eb7fa07a354a18fc7bf1eb0ddc46d5533c4e0 |
| app/experiments/accumulation_probe/reaudit_stage0.py | 14710 | 0o644 | 02d8e0f5b45fa28ba165ba9ce641a8dff7d19260382536d94e404dc1f5972d69 |
| app/experiments/accumulation_probe/run_arm.py | 2838 | 0o644 | a752f2e206f76d265443f404d489dce43dad4f2800de02f0c33f74c130b42383 |
| app/experiments/accumulation_probe/run_gen.py | 2045 | 0o644 | 92dad922bc82e3fce03410c0630749595f7cf2a712ecf1dc67b3fca5f4671c02 |
| app/experiments/accumulation_probe/stage0.py | 3656 | 0o644 | 16fd2f42e3d02a1a370b1daa87e494c7e481effc628703df37c303f7bb7e1ac0 |
| app/experiments/accumulation_probe/tasks.py | 20640 | 0o644 | e73d790cdb7fa494db84cc22dc0a16250e35f7d6907e9ac27ef6562fbe73ea38 |
| app/experiments/accumulation_probe/tasks_v2.py | 23246 | 0o644 | b2229e9f3ab6cff3f827305106d6525a0992ac68fd4d484ab6952f7f3bfa9702 |
| app/experiments/accumulation_probe/val_select.py | 1731 | 0o644 | ebfaa7a2b218966315554dcb16653865ad9c013d3a2bfbe5e6a80f0d81c7d21a |
| app/experiments/accumulation_probe/worlds.py | 3742 | 0o644 | 9d495f967808ff8a175794ed8373f161f6703c45289015f97aff1f7df214c56f |
| app/maintenance/night_cycle.py | 14825 | 0o666 | eea65c8a6a82be1f9a8c51bb9c44cbbb63e7c75ccf23b1ec6381aa2190d09cce |
| audits/2026-09-14_tier5_followup_experiment_design.md | 23099 | 0o644 | 9c3d97b2d07a7b1a3e6946a2e904fed64e3088feebe2cbdd9bc58f4ef6b6af70 |
| audits/2026-09-21_ap0_stage0_preregistration_v1.md | 11532 | 0o644 | f8d8dd184cea3c87b730165d57a61f9125a15b4053ced9bce999fbc13ec55850 |
| audits/2026-09-21_ap0_stage1_preregistration_v2_DRAFT.md | 19972 | 0o644 | 456a8d50f8199478fd8c45166b4f36414c8198266cea62eb24bd837d59fbc513 |
| audits/2026-09-21_ap0_v2_causal_chain_and_skeptic_review.md | 11359 | 0o644 | 520eae879c17f49b82cd03784960885015394d5c8bc8a32d9e92f1754d342713 |
| audits/2026-09-21_ap0_v2_constructor_qualification_protocol.md | 9646 | 0o644 | 3e5d6f3f938d3b9a3cf8be5930de69e5581117c189f11611ea3a13ef1f5006c6 |
| claude_relay/.last_seen_from_air.json | 74 | 0o644 | f8e972bb7115f439795abddbba0d7d96d49aad2e8eadbc782694f4306e4b62d4 |
| claude_relay/README.md | 7716 | 0o644 | 9a5a3210815550709486ce69d49487a9606d5d7f65769d224ebc0fbb59c96452 |
| claude_relay/from_m5.md | 192154 | 0o644 | 43c0d1f1d27f0115954c997d4995454c27d83962956d4d5adba006eac22d6c31 |
| claude_relay/relay.py | 18594 | 0o644 | 17d1a9809c85e41f72c07cc14af63a430460df85408d61fa0ab99cd6cedaf437 |
| data/faiss.index | 10952749 | 0o644 | 65903b32b3a5a5353f3f92253e0ee39ff0e825910e2025ac8631282e5b9b5863 |
| data/memory_meta.json | 6587816 | 0o644 | 7c6c2d7ddd69957f0a4a234e07f0f944bcc1620e8c5c092694534c98b03584de |
| logs/janitor_report.json | 13277 | 0o644 | 09db229c008e96985e2572c394f6365f2492c801b07611f37f110e98ca4feb3e |
| memory/experiments/accumulation_probe/stage0/FREEZE.json | 6687 | 0o444 | 43aca7d451a259299a2e128521130bd6b861f51275990878c42e22ef3e1c0522 |
| memory/experiments/accumulation_probe/stage0/FREEZE.sha256 | 78 | 0o644 | 85b8d2e5cce011269ebcf2ff625ef0a931c85f5eed66e09e5d1d7b935fb35d95 |
| memory/experiments/accumulation_probe/stage0/oracle/hidden_tests.json | 142249 | 0o444 | 45fda3f4b615edecf525f59143ffaf70b106b4cd7073966474cf3fdaae0c00ab |
| memory/experiments/accumulation_probe/stage0/oracle/task_meta.json | 15153 | 0o444 | 024361c2d3c3936d592d2ce8c70ecdf848924f8356979edb76c6ab3709fb0836 |
| memory/experiments/accumulation_probe/stage0/oracle/worlds.json | 1625 | 0o444 | 2075b9341abb7c59c8ead81d3a3ed2e70efb810cbcce6682079920630a10e538 |
| memory/experiments/accumulation_probe/stage0/progress.log | 3859 | 0o644 | 8affa292f8c33ad2eae3273465076b97b7f609e70de6bdcf879506803649df7b |
| memory/experiments/accumulation_probe/stage0/public/public_tasks.json | 12401 | 0o444 | 6af821a5315d4f3d8a83e492da0388b33ad133e285488b617cfde7187b395397 |
| memory/experiments/accumulation_probe/stage0/reports/import_audit.json | 5840 | 0o444 | 9697c9baf11476b7639e2cd60b22c884dc28dbb5d9976ccf7587a6711ae14c5a |
| memory/experiments/accumulation_probe/stage0/reports/jail_probes.json | 5066 | 0o444 | 5a11b3bd9b5e9230152bff8222450302aa88650634fa972b14bf37233052d624 |
| memory/experiments/accumulation_probe/stage0/reports/leakage.json | 743 | 0o444 | 7caa8cd30f8b1f65d6b149f9fa3b3792a890eb60a7c6c68f22c65519da769a7b |
| memory/experiments/accumulation_probe/stage0/reports/oracle_qualification.json | 5063 | 0o444 | 1c79644e6a07724caa410d180a27e84a89b70985dd99c7155bac9407494d0768 |
| memory/experiments/accumulation_probe/stage0/results/posthoc_addendum/addendum.json | 1269 | 0o644 | 7c05298978f75d24f631bd1448cce6606014f43559d849a61f1f12585a916d01 |
| memory/experiments/accumulation_probe/stage0/results/posthoc_addendum/addendum.py | 2764 | 0o644 | 422e75e80a847ae35286c7e8deac5e67b3b2538f2d6b2d085b78c378aeca1b90 |
| memory/experiments/accumulation_probe/stage0/results/primary/grades.jsonl | 238174 | 0o644 | 01e71a7d6c5e670fc7903c1e8b550541e492a4b1c5ce4d29239210d8573e2385 |
| memory/experiments/accumulation_probe/stage0/results/primary/metrics.json | 9788 | 0o644 | 1d2523b451e9c8fe5c30ebbd2d2cc04ce464bab6838f8c4e5ceb22537d4dea1d |
| memory/experiments/accumulation_probe/stage0/results/reaudit/reaudit.json | 6277 | 0o644 | 38502934e5b6d0f8c8e7ecffda073b1e59559b031c56947ffece414bec4b6e51 |
| memory/experiments/accumulation_probe/stage0/results/reaudit_r2/reaudit.json | 6963 | 0o644 | baa61196d763f2820baf8719879e9c3608888e0e034cd785616dfbc9b6c7c54f |
| memory/experiments/accumulation_probe/stage0/runs/E/calls.jsonl | 138507 | 0o644 | ad8f0a7462dfdc280b487c71f23d6c605423dddaf6bc564097f90178d0b707cd |
| memory/experiments/accumulation_probe/stage0/runs/E/inputs/public_tasks.json | 12401 | 0o444 | 6af821a5315d4f3d8a83e492da0388b33ad133e285488b617cfde7187b395397 |
| memory/experiments/accumulation_probe/stage0/runs/E/jail_probe.txt | 1 | 0o644 | 2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881 |
| memory/experiments/accumulation_probe/stage0/runs/E/plan.json | 47063 | 0o444 | b83f0996c865ea6cc4338c4168865fd8d117cc21c7f0366086e0855ef398b02c |
| memory/experiments/accumulation_probe/stage0/runs/H/calls.jsonl | 244944 | 0o644 | bcdf8b6cb62a7a9748114e2f697f3247f777867b81e2da4a540d710c61ae5ad7 |
| memory/experiments/accumulation_probe/stage0/runs/H/inputs/public_tasks.json | 12401 | 0o444 | 6af821a5315d4f3d8a83e492da0388b33ad133e285488b617cfde7187b395397 |
| memory/experiments/accumulation_probe/stage0/runs/H/jail_probe.txt | 1 | 0o644 | 2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881 |
| memory/experiments/accumulation_probe/stage0/runs/H/plan.json | 80265 | 0o444 | e6d6365941405a3f51f6ce307c04753692a309844822b0743f3b2502b5a84031 |
| memory/experiments/accumulation_probe/stage0/runs/H2/calls.jsonl | 127312 | 0o644 | a6b29c835a9b5c7da14b69dee5a9eb999a1e213e3f86f3897aede7bd867261f8 |
| memory/experiments/accumulation_probe/stage0/runs/H2/inputs/public_tasks.json | 12401 | 0o444 | 6af821a5315d4f3d8a83e492da0388b33ad133e285488b617cfde7187b395397 |
| memory/experiments/accumulation_probe/stage0/runs/H2/jail_probe.txt | 1 | 0o644 | 2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881 |
| memory/experiments/accumulation_probe/stage0/runs/H2/plan.json | 38853 | 0o444 | 9773c08831cdb42d5c354011d9d133614c6d78c5089dd4b6b8cf2a6df18eecf8 |
| memory/experiments/accumulation_probe/stage0/runs/IC/calls.jsonl | 117960 | 0o644 | da63bad4d8d652fc062c3879731b6e9d8f0ea15968c46f8bad60e4aad2c4e1d4 |
| memory/experiments/accumulation_probe/stage0/runs/IC/inputs/public_tasks.json | 12401 | 0o444 | 6af821a5315d4f3d8a83e492da0388b33ad133e285488b617cfde7187b395397 |
| memory/experiments/accumulation_probe/stage0/runs/IC/jail_probe.txt | 1 | 0o644 | 2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881 |
| memory/experiments/accumulation_probe/stage0/runs/IC/plan.json | 31890 | 0o444 | 84f0be5de9e4fa65868e5766936a59aef47cbeec6492e8502b1615f52d70190e |
| memory/experiments/accumulation_probe/stage0/runs/MISMATCH/calls.jsonl | 129956 | 0o644 | 47d8fb8ba48f5fbbc57e715784bef5774773c82bf562d6629bb24e53a1780520 |
| memory/experiments/accumulation_probe/stage0/runs/MISMATCH/inputs/public_tasks.json | 12401 | 0o444 | 6af821a5315d4f3d8a83e492da0388b33ad133e285488b617cfde7187b395397 |
| memory/experiments/accumulation_probe/stage0/runs/MISMATCH/jail_probe.txt | 1 | 0o644 | 2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881 |
| memory/experiments/accumulation_probe/stage0/runs/MISMATCH/plan.json | 39186 | 0o444 | 4dcc7dcec3588f897d97bd9fcde8d94cb1852479f01ff1739975a5ca1d67de02 |
| memory/experiments/accumulation_probe/stage0/runs/N/calls.jsonl | 150408 | 0o644 | 5ed8e9cffef4652729e1876f4b435d8b246e65fe5cfe33bc1c108dee14a32907 |
| memory/experiments/accumulation_probe/stage0/runs/N/inputs/public_tasks.json | 12401 | 0o444 | 6af821a5315d4f3d8a83e492da0388b33ad133e285488b617cfde7187b395397 |
| memory/experiments/accumulation_probe/stage0/runs/N/jail_probe.txt | 1 | 0o644 | 2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881 |
| memory/experiments/accumulation_probe/stage0/runs/N/plan.json | 18636 | 0o444 | 6a0e48aa2cdc440c245411b314bd1c7914a6bb493c4a3387bcd9c268ef6c5b59 |
| memory/experiments/accumulation_probe/stage0/runs/N2/calls.jsonl | 96075 | 0o644 | 40d81679fde9327ba9a07dea5bef0d679b4d69400a2ecd8bba67cb953f6c7fae |
| memory/experiments/accumulation_probe/stage0/runs/N2/inputs/public_tasks.json | 12401 | 0o444 | 6af821a5315d4f3d8a83e492da0388b33ad133e285488b617cfde7187b395397 |
| memory/experiments/accumulation_probe/stage0/runs/N2/jail_probe.txt | 1 | 0o644 | 2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881 |
| memory/experiments/accumulation_probe/stage0/runs/N2/plan.json | 11547 | 0o444 | 4668c1f417ef596c5670fdab4dc7f0e06ff3b392f5cc019960b5cba9dcaa0a77 |
| memory/experiments/accumulation_probe/stage0/runs/NEUTRAL/calls.jsonl | 193711 | 0o644 | a34768376e0de6d33261cf130125895ce52ba44a2132ee73773411d188de1f3b |
| memory/experiments/accumulation_probe/stage0/runs/NEUTRAL/inputs/public_tasks.json | 12401 | 0o444 | 6af821a5315d4f3d8a83e492da0388b33ad133e285488b617cfde7187b395397 |
| memory/experiments/accumulation_probe/stage0/runs/NEUTRAL/jail_probe.txt | 1 | 0o644 | 2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881 |
| memory/experiments/accumulation_probe/stage0/runs/NEUTRAL/plan.json | 61370 | 0o444 | 17e411405c8ae40e1b6ff31c5222cdf882463fd30e26466018192f445231c662 |
| memory/experiments/accumulation_probe/v2/dev/calls.jsonl | 109282 | 0o644 | 0209c5cf9510945f54c9ada239935740f7f2650dbb4c42f42f11d4bfc9c684c0 |
| memory/experiments/accumulation_probe/v2/dev/dev_summary.json | 2599 | 0o644 | e38f2ed3e20b322ee80aa00e9030ab804dd0c5b515e837f56c71f3d5dfb02488 |
| memory/experiments/accumulation_probe/v2/dev/task_meta.json | 33291 | 0o644 | c53caf3131b70ce1d466bf588b6ad0aeb0d959ca225eb93f72cf6aa6c9bd26eb |
| memory/experiments/accumulation_probe/v2/dev/val_selection_detail.json | 1722 | 0o644 | 4fc6eff0702731c9a776c3d3e9133ff97963292aa69731d9b24b1443a0cfabac |
| memory/experiments/accumulation_probe/v2/dev/val_templates.json | 170 | 0o644 | c0133da65eb5b8c51cf8705367bf7022858ed82bd8e46e8e9cc3610e24bbf497 |
| memory/experiments/accumulation_probe/v2/dev/val_templates_pooled.json | 170 | 0o644 | 334500f31b4b59fab2eef5c9327c605afb186989a17a61c47c2a8a493e0bcc22 |
| memory/experiments/accumulation_probe/v2/dev/worlds.json | 1625 | 0o644 | 6954542d0dc567e33c7fe841febb40b2d142dea1756aae0c560cd60760e6f143 |
| memory/experiments/accumulation_probe/v2/qual/FREEZE_QUAL.json | 3950 | 0o644 | cf184d8616f33693dc75b344a382f6ea5458e2ee929204c5a598b8f352b40e7d |
| memory/experiments/accumulation_probe/v2/qual/GATE_INPUTS.json | 225 | 0o644 | 18834732f6b947f08fd8ad7c6907aece5d8384e88ead4dc971d693eaac06e3ee |
| memory/experiments/accumulation_probe/v2/qual/QB_FREEZE.json | 842 | 0o644 | 493d8693b03c59c95fbab25ef7fcdfe89fdefce7f9ad56c0246f9cfd99d14d77 |
| memory/experiments/accumulation_probe/v2/qual/hand_adjudication.json | 2304 | 0o644 | 9fbe8efa3138aca45d5bb7dd87a9919699d558aa9c29e731a4da31f9f7b25dc0 |
| memory/experiments/accumulation_probe/v2/qual/oracle/meta.json | 8039 | 0o644 | ae4c5d1fdf2f9545db59a2c32f81f11b266188cade277bede16dd687e1edb1d8 |
| memory/experiments/accumulation_probe/v2/qual/oracle/val_tests.json | 88869 | 0o644 | b73807a27b40ecfbcdbb26bbfd4eb6020b846507a5392860c8fd1b114fe47ddc |
| memory/experiments/accumulation_probe/v2/qual/oracle/worlds.json | 1606 | 0o644 | d4d12eef2695b63aecd3b810a8c002500157df3e2e0c20d6c735e131e70e3dcb |
| memory/experiments/accumulation_probe/v2/qual/results/posthoc_auditor_v2/drafts_audited.json | 57211 | 0o644 | 7a7e995ce601150638f61cf45130718da9d615e905379141fbba744aeec0c63f |
| memory/experiments/accumulation_probe/v2/qual/results/posthoc_auditor_v2/summary.json | 4659 | 0o644 | 80ea8dd290c3461f8f5548d980f8646c32e30c0d425176b8679b7867731cc71a |
| memory/experiments/accumulation_probe/v2/qual/results/primary/drafts_audited.json | 57833 | 0o644 | bb557cba1b92d96e3fef53dc8569798d8e0d5838855a53cefbb3fa325d738079 |
| memory/experiments/accumulation_probe/v2/qual/results/primary/summary.json | 4641 | 0o644 | b561fe3520db57f681ca69f03709f7765479b7389a9a4e7a52a2b02e0a6562cd |
| memory/experiments/accumulation_probe/v2/qual/results/qb/drafts_audited.json | 6216 | 0o644 | 33bd8776c0765ebdc1b42620d398e807f7dbd3392de2eaf8df8945b608f7b040 |
| memory/experiments/accumulation_probe/v2/qual/results/qb/summary.json | 386 | 0o644 | c341d93a5f0eff118c366ef4fc8816ecec923fa45322abce89dadd1070891835 |
| memory/experiments/accumulation_probe/v2/qual/roots/construct/calls.jsonl | 183247 | 0o644 | c7421da668604a2e52a60ddf109355ae09a092d1aeb41093edfc4f77b412f620 |
| memory/experiments/accumulation_probe/v2/qual/roots/construct/inputs/requests.json | 120423 | 0o644 | 3e1f0a5474bb9e95846fecee278ac047ee0c6102b37e3d5f3703d8207691c956 |
| memory/experiments/accumulation_probe/v2/qual/roots/gate/calls.jsonl | 1027426 | 0o644 | 98c81d07c513806260919af053c12fb59123e5733dacf8b6990513b41a6874fc |
| memory/experiments/accumulation_probe/v2/qual/roots/gate/inputs/gate_meta.json | 57410 | 0o644 | 360d023f7347d53c58dc2dff5770c03923f17cbd2d20613f51166a57037301bc |
| memory/experiments/accumulation_probe/v2/qual/roots/gate/inputs/requests.json | 596129 | 0o644 | 3fb7db7a148d39c93a98fd58a2f0171d68b02e6b6303bc6c13e4dd711fe20bc6 |
| memory/experiments/accumulation_probe/v2/qual/roots/qb_construct/calls.jsonl | 24276 | 0o644 | 080e680eacabd4ac33ec7eef858d1cc53e855919baca11390c133624afae500b |
| memory/experiments/accumulation_probe/v2/qual/roots/qb_construct/inputs/requests.json | 16701 | 0o644 | 20e639f42a9cec27c95019bc5539049d886703c6082b93fb2bda1ee605c64439 |
| memory/experiments/accumulation_probe/v2/qual/roots/qb_gate/calls.jsonl | 55991 | 0o644 | b4a8526e304b0fee660bafb02bcb713723cc90f39c725b58b9a37879ccd2ccda |
| memory/experiments/accumulation_probe/v2/qual/roots/qb_gate/inputs/gate_meta.json | 3266 | 0o644 | 68bedc06131de8464f35a8bcb9e41f0c583f66997c08f96b4908a7bc9f9546a9 |
| memory/experiments/accumulation_probe/v2/qual/roots/qb_gate/inputs/requests.json | 34815 | 0o644 | 9476af61ac303f49ceebbaf05346e32e9fe61b994be9103f97615d8f7b775775 |
| research/OPEN_QUESTIONS.md | 28220 | 0o644 | d83812a009ea016f435b8185a8138a0b9a421b79e7760c438ee67afdf9837024 |
| run.py | 68780 | 0o755 | 78d1ba29f88b6d9e6d1802899a029db372c82f9a6e6e7ea384686857cbac4ea1 |
| sandbox/safe_exec_wrapper.py | 33060 | 0o644 | 7605102d2eb0b9a25c6e5e2704a1efff849a06743334160c4e92a84b170f8cc7 |
| sandbox/scripts/temp_self_edit.py | 263 | 0o644 | f5cde4ec6652dfe07ef21e97a0e92da36695552e6627a981370ac4976e5d58f4 |
| scripts/verify_accumulation_probe.py | 15463 | 0o644 | 1dda48525e8b6b418fe64009df7b5ad5b4f597c14844740965442a7241baf603 |
| scripts/verify_accumulation_probe_v2.py | 14579 | 0o644 | 6afef26d53b1fbea1915969cc264651ae42d453e27e337a065c1b1362d7a229b |
| scripts/verify_liveness_ledger.py | 96819 | 0o644 | c93ce499ef7ff655a002b22c5735ebe22a0194457e27e1229b52af93222019a9 |
| scripts/verify_provenance_check.py | 60552 | 0o644 | 23862b8aa64b65b1ceca1c3e467ec678b629b5a78904312c36ece27dd175d895 |
| scripts/verify_qual_ident.py | 8724 | 0o644 | b3e12799af0943d5de73f2ff07db1ef10fae85fed351b1c2fed6debf06428981 |
| staging/self_edit_candidate.py | 178 | 0o644 | 173382a2b1e0841c2d12a55d5a0ad958e126c76c491739641307dd62c50277d4 |

</details>

## Appendix C. Primary-source navigation and reproducibility

The findings above were reconstructed from these sources before dedicated reviewer narratives, subject to the disclosed embedded-draft exception. Links use the audited local workspace.

| Evidence | Principal files |
|---|---|
| Stage 0 design/freeze | [Protocol](/Users/richietate/Desktop/FeralEcho/audits/2026-09-21_ap0_stage0_preregistration_v1.md), [FREEZE](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/stage0/FREEZE.json), [freeze sidecar](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/stage0/FREEZE.sha256) |
| Stage 0 raw outcomes | [N ledger](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/stage0/runs/N/calls.jsonl), [H ledger](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/stage0/runs/H/calls.jsonl); corresponding E, IC, H2, N2, NEUTRAL and MISMATCH directories contain their own plans and ledgers |
| Stage 0 expected answers | [Hidden tests](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/stage0/oracle/hidden_tests.json), [worlds](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/stage0/oracle/worlds.json), [task metadata](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/stage0/oracle/task_meta.json) — Stage 0 only |
| Generation, seeds, request structure | [common.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/common.py:23), [prompts.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/prompts.py), [run_arm.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/run_arm.py), [run_gen.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/run_gen.py), [ollama_client.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/ollama_client.py) |
| Public schemas, teaching examples, privileged identifiability | [tasks.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/tasks.py:95), [constructor.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/constructor.py:7), [worlds.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/worlds.py) |
| Grader access defect | [shared _CASES scaffold](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/tasks.py:246), [candidate/test concatenation](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/oracle_runner.py:41), [execution profile](/Users/richietate/Desktop/FeralEcho/sandbox/echo_sandbox.sb), [wrapper](/Users/richietate/Desktop/FeralEcho/sandbox/safe_exec_wrapper.py) |
| Generation confinement | [jail.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/jail.py:6) |
| Stage 0 statistics/decision rules | [grade.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/grade.py:12), [re-audit implementation](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/reaudit_stage0.py) |
| Development and validation selection | [raw dev calls](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/dev/calls.jsonl), [val_select.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/val_select.py), [pooled selection](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/dev/val_templates_pooled.json) |
| QA qualification | [QUAL protocol](/Users/richietate/Desktop/FeralEcho/audits/2026-09-21_ap0_v2_constructor_qualification_protocol.md), [FREEZE_QUAL](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/FREEZE_QUAL.json), [qual.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/qual.py:97), [raw constructor calls](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/roots/construct/calls.jsonl), [raw gate calls](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/roots/gate/calls.jsonl) |
| QB qualification | [QB_FREEZE](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/QB_FREEZE.json), [qb.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/qb.py), [raw QB calls](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/roots/qb_construct/calls.jsonl), [raw QB gate calls](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/roots/qb_gate/calls.jsonl) |
| QUAL expected answers | [val_tests.json](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/oracle/val_tests.json), [worlds.json](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/oracle/worlds.json) — qualification only |
| Corrective exactness interpretation | [audit_v2.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/audit_v2.py), [qual_posthoc.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/qual_posthoc.py), [hand adjudication](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/hand_adjudication.json) |
| Symbolic diagnostic and attacks | [qual_ident.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/qual_ident.py), [diagnostic tests](/Users/richietate/Desktop/FeralEcho/scripts/verify_qual_ident.py), [v2 task/case generation](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/tasks_v2.py:164) |
| Prospective design and reviewer comparison | [Stage 1 draft](/Users/richietate/Desktop/FeralEcho/audits/2026-09-21_ap0_stage1_preregistration_v2_DRAFT.md), [causal/skeptic review](/Users/richietate/Desktop/FeralEcho/audits/2026-09-21_ap0_v2_causal_chain_and_skeptic_review.md) |

Independent numerical reconstruction did not import repository modules. The functional regrade traversed recorded responses, extracted the requested function, evaluated each outside the test-answer namespace, and stopped on the first differing/exceptional hidden case. Bootstrap comparisons resampled task-level paired rates with the frozen seed and number of resamples. The identifiability counterexamples and scorer attack are specified in §§6–9 so their reasoning does not depend on a generated report or opaque verifier.

The 318 original mutants and 77 later text-mutant variants were evaluated as existing pure program definitions in the audit interpreter. Original mutants were all killed; three later variants survived: K1.T3 sorted→list, K2.N1 name tie-break→negative name length, and K3.T3 maximum initialized to zero. These reflect coverage gaps, not contradictory stored answers. Mutation survival is evidence against completeness of a test set, not evidence that a historical model used the mutant.

This report contains no Stage 1 secret and no new acquisition implementation.

## Final verdicts

**AP-0 EVIDENCE INTEGRITY:** ACCEPTABLE WITH CAVEATS

**CURRENT LEARNING CLAIM:** NOT ESTABLISHED

**PROPOSED STAGE 1:** NOT READY

**NON-LEARNING DOPPELGÄNGER:** SURVIVES

**SELF-SUFFICIENCY IMPLICATION:** LIMITED

**RECOMMENDED NEXT ACTION:** Pre-register a fresh-world schema × representation qualification with a fixed compiler baseline and an answer-isolated scorer.

## Conceptual addendum — minimum longitudinal discrimination experiment — 2026-09-22

**Prospective design only. No audit reopened, apparatus changed, code written or experiment run.** The target is improvement in acquisition competence at the system level, not necessarily a change to its underlying algorithm.

1. **Experimental unit.** An independently sampled acquisition history, paired with novel evaluation worlds. Fork identical initial systems within each unit for controlled comparisons. Replicate histories; calls, seeds and test cases within a history are not independent experimental units. Include at least two prospectively held-out rule families, with a declared transferable structure that could make earlier experience useful.

2. **Sequence of acquisition cycles.** Use two cycles: acquire in family A, then family B, retaining checkpoints S0, SA and SAB. A separate branch acquires B directly from S0, producing SB. This latest-experience-only control distinguishes accumulation from a benefit supplied entirely by B. Evaluate checkpoints on matched novel problems in disposable forks; probe outputs and feedback never return to any continuing acquisition history. Freeze the design before acquiring A or inspecting probe results.

3. **Restart/context boundaries.** Restart between acquisition cycles and before every probe. Clear conversational context, transient agent state and model-serving context. Start each novel problem independently from its assigned checkpoint. Only explicitly committed persistent artifacts cross boundaries; neither evaluator state nor previous probe solutions cross them.

4. **Allowed persistent state.** Freeze model weights, executable apparatus and human-authored policies. Separate task records R—examples, mappings and task-specific solutions—from system-produced transferable state G, such as hypothesis-selection, experiment-selection or verification procedures. G must exclude old task entries, identifiers and world parameters; its format and capacity are fixed prospectively. The decisive probes receive **G alone**, with R and acquisition transcripts inaccessible. Include R-only and reset controls. No human edits to acquired state are allowed.

5. **What later problems withhold.** Withhold evaluation families from acquisition, tuning and strategy selection. Use new rule structures, identifiers and independently sampled parameters, not renamed instances of old rules. Supply no family-specific solution template or answer-bearing carrier. All conditions receive the same public task interface, admissible hypothesis language and opportunities to obtain evidence. This must be a learnable task with a declared basis for generalization; withholding an essential schema would recreate K3's ambiguity. Hidden scoring answers remain outside the learner and candidate execution environment.

6. **Primary improvement measure.** Predeclare a mastery criterion on hidden new inputs and measure labeled observations/interactions needed to reach it, under equal inference-compute and interaction budgets. Use mean capped query cost, counting nonattainment at the fixed failure penalty, and report attainment rates alongside it. The primary comparisons are GAB against G0, GA, GB and the fixed-compiler baseline on matched novel worlds, clustered by history. **Reduced sample complexity on prospectively novel rule families is a useful primary endpoint:** it directly measures acquiring later capabilities more efficiently. It is convincing only with matched accuracy, compute, evidence access and failure accounting; fewer examples bought with more computation or easier tasks do not establish it.

7. **Fixed-compiler baseline.** Freeze a competent general acquisition/compiler implementation before the histories. Give it the same public language, budgets and access to all accumulated task records and episodes. Permit its ordinary retrieval, composition and hypothesis search; do not cripple it to make novelty difficult. Its acquisition procedure remains fixed. This baseline tests whether stored task information processed by an already available mechanism explains the apparent improvement.

8. **Decisive result patterns.** H0 survives if gains disappear when R is withheld, are matched by the fixed compiler, or SAB offers no reproducible acquisition advantage beyond SA/SB. H1 receives support if GAB alone reduces novel-family acquisition cost beyond all specified controls, with contributions from both cycles. Removing G should remove the advantage; restoring it after restart should restore it. Require a prospectively meaningful effect with uncertainty excluding the null. A null result with weak precision, ceiling effects or unrelated families is inconclusive, not proof of H0.

9. **Strongest remaining alternative.** A fixed, pre-existing meta-learning mechanism could interpret G and activate capabilities it already possessed. Even this positive result would not establish invention of a new learning algorithm or foundation-model improvement. It would reject the specified task-state-only explanation and establish improved effective acquisition competence. “Fixed algorithm” and H1 are compatible: the hypotheses differ in whether prior experience improves later acquisition behavior, not merely whether code changes.

10. **Minimum evidence for “persistent accumulated competence.”** Require replicated causal benefit from at least two acquisition cycles, survival of restart, improved acquisition on independently held-out families, superiority to task-record-only and fixed-compiler controls, and loss/restoration of the benefit under acquired-state ablation/restoration. Preserve all attempted histories and failures. The defensible phrase is **“persistent accumulated competence within the tested task distribution, at the system level.”** More stored rules, one successful transfer, or improved scores without these controls are insufficient.
