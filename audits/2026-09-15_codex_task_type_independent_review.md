# Independent review of the September 14 task-type research arc

Date: 2026-09-15. Reviewer: Codex, independent replication/adversarial review. Scope: repository evidence and preserved local artifacts; no new model experiment, production imports, or production execution.

**The narrow result survives: the saved coding-condition outputs scored higher, not lower, on the chosen specificity measure. The broader council conclusion does not survive this audit. Condition A was not direct: it ran the same council treatment as B. Complete production isolation is also not established, because an unpatched salience computation has a production write path. Historical TOOL-LIST delivery was inferred from a gate without proving that its registry was populated.**

## 1. Opening integrity record

Recorded before investigation:

- Working directory: /Users/richietate/Desktop/FeralEcho.
- Git HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce`.
- Path count: **22,284**, defined as `find . -print | wc -l`, including root, directories, ignored files, and .git paths; not a tracked-file count.
- Runtime: **active**. Initial sandboxed `ps` was denied; an approved read-only process listing showed PID 7636 running start_echo.sh, PID 7644 running `python -u run.py`, PID 7645 logging via tee, and PID 87918 running `python -m echo_studio.main`. Ollama/llama-server was also active. No process was signaled, attached to, stopped, restarted, or intentionally altered.
- The working tree was already dirty. Its full opening status is preserved in Appendix A. These changes predate this review.
- No applicable AGENTS.md was found in the repository search. No production or experiment module was imported by this review. Analysis used read-only JSON/text parsing and independent arithmetic in Python with bytecode writing disabled.

The source tree is not identical to HEAD: river_deliberation.py is modified, and all three experiment scripts are untracked. A common HEAD therefore does **not** establish identical executed source across historical production, experiment, and review. The inspected river_deliberation diff concerns fallback selection and a Counter import; it does not alter the direct gate, templates, or the salience call discussed below.

## 2. Evidence sources and research arc

Local source IDs used throughout:

| ID | Primary source / locator |
|---|---|
| H1 | memory/interaction_log.jsonl:20170, trace b073d789-b889-4bd3-bc58-ccfd375044e3 |
| H2 | memory/council_deliberations.jsonl:5006, same trace |
| H3 | memory/synthesis_integrity_log.jsonl:3486, same trace |
| R1 | audits/2026-09-14_core_task_misclassification_council_synthesis_trace.md |
| R2 | audits/2026-09-14_task_type_downstream_behavior_archaeology.md |
| R3 | audits/2026-09-14_task_type_behavioral_experiment.md |
| G | scripts/task_type_behavioral_experiment.py |
| J | scripts/task_type_behavioral_experiment_judge.py |
| A | scripts/task_type_behavioral_experiment_analyze.py |
| O | app/core/echo_model_orchestrator.py, especially 464–616, 1499–1535, 1716–1737 |
| D | app/core/river_deliberation.py, especially 295, 314–393, 397–493, 1086–1515 |
| T | app/core/tool_manager.py; run.py:1341–1354; app/core/awareness_tools_integration.py |
| S | app/core/echo_core.py:682–793 |
| E | /private/var/folders/vg/3mw0sd2j7f12frh367wggw340000gn/T/task_type_behavioral_experiment_20260914_3bd4ed27/ |
| L | /private/tmp/ttbe_main_run.log; /private/tmp/ttbe_judge.log |

E contains raw_trials_anonymized.jsonl, condition_map_SEPARATE.jsonl, judge_scores_anonymized.jsonl, run_metadata.json, and analysis_result.json. The separate dd7c51fa directory exists but is empty: G creates an initial random evidence directory before applying TTBE_EVIDENCE_DIR. The historical response also survives at /private/tmp/real_turn5_response.txt. These files were read, not rerun or rewritten.

The arc is: a fifth conversational response was judged generic relative to preceding turns; H1 recorded coding and quality_score=1; H2/H3 recorded three councillors and accepted synthesis. R1 identified keyword routing and correctly weakened the quality-score argument. R2 traced templates and TOOL-LIST, but overstated historical delivery of the latter. G attempted a direct/council/task-type decomposition; J rated final text; A computed summaries; R3 reported no negative specificity effect. This review reproduces the summaries while discovering that the direct comparison never existed.

The alleged external safety incident in the frozen prompt is **user-supplied experimental material**, not a fact independently established by this repository review. No conclusion here endorses its truth.

Evidence vocabulary: **OBSERVED** means present in a primary artifact; **SUPPORTED** means convergent evidence with material gaps; **REPRODUCED** means independently recalculated here, not a new generation; **INFERRED** means derived from code plus assumptions about runtime; **SPECULATIVE** means an untested causal possibility; **FALSIFIED** means directly contradicted within the stated scope. These labels are not interchangeable.

| CLAIM | SOURCE | DIRECTLY OBSERVED? | INFERRED? | REPRODUCED? | CONFIDENCE | NOTES |
|---|---|---|---|---|---|---|
| Historical turn logged coding | H1–H3 | Yes | No | Matching records checked | High | OBSERVED; not inferred from output style |
| Keyword rule yields coding | O:464–616; H1 prompt | Source and text | Historical rule applicability | Arithmetic/hits yes | High | REPRODUCED: code/python/program=3; reason/evaluate=2; yourself=1; general=.1 |
| Coding bypasses the personal direct gate | D:295,1162; H2/H3 | Source and actual council | Counterfactual personal route | No live replay | High | SUPPORTED causal routing; selected model identities observed |
| Task type changes synthesis instructions | D:314–393,1402–1412 | Yes, source | Historical HTTP delivery | No packet capture | High | Mechanism verified; exact historical request not preserved |
| Historical TOOL-LIST was delivered | O:1509–1517; T | Gate only | Yes, registry/import success | No | Medium at most | INFERRED, not confirmed by H1–H3 |
| Experimental TOOL-LIST absent | E metadata; L:23 | Yes | No | Cross-checked source | High | OBSERVED null, 0 characters |
| A was a direct control | G; E intercepts; L:21 | Contradictory evidence | No | Call sequence checked | High | FALSIFIED |
| A/B list difference measures council effect | Same sources; raw outputs | Rates yes; treatment no | Invalid causal inference | Rates yes | High | Causal attribution FALSIFIED; A and B both council |
| C specificity 5 vs B 4.33 | E raw/map/judge files | Yes | No | Yes | High | REPRODUCED descriptive scores |
| Template degrades this endpoint | E; J | No | Hypothesis | No new generation | Low | NOT SUPPORTED; observed direction opposite |
| Historical candidates were already list-heavy | H2 full response_raw | Yes | Genericness is qualitative | Text comparison | High for lists | OBSERVED content; semantic quality not objectively established |
| quality_score=1 measures bad prose | echo_quality_scorer.py:344–375; H1 | Contradiction | No | Branch inspected | High | FALSIFIED for this nonempty, code-free output |
| Counter detects actual leaked writes | G:149–190,408–414 | Contradiction | No | 65 intercepts counted | High | FALSIFIED; diagnostic counts intercepted attempts |
| All production state was untouched by experiment | G; D:1224–1232; S | Unpatched write path | Actual write success | No | Low | UNRESOLVED; positive counter is not the issue |
| TOOL-LIST changes behavior or interacts with template | No controlled comparison | No | Yes | No | Low | SPECULATIVE, scientifically testable |

The earlier September 9 classifier-labeling work is a distinct question. R1's Tier-4 coding-correctness findings are background hypotheses, not replications of reflective conversational quality; their headline numbers are not used as independent evidence for this turn.

## 3. What the experiment actually manipulated

### Fatal control defect

G calls disable_direct_echo_bypass_for_personal(rd) **once before either trial loop**. That function sets D.DIRECT_ECHO_TASKS to an empty frozenset. original_direct_tasks is only saved to metadata, never restored. run_condition_trial assigns personal and base_system to **both A and B**; it contains no routing override for A.

This is not merely a suspected code bug. L records permanent clearing. The 15 main trials contain 45 intercepted RiverBrain.learn calls, 15 council-log calls, and five coding integrity-log calls: **65** total. Each A trial has learning previews for qwen2.5-coder, llama3.1, and Echo, followed by council logging. Under the claimed design the normal accepted paths would produce 10+20+25=55 intercepts, not 65. A trial cd86616e even begins “The council's perspectives have shed new light...”. The call evidence is decisive; the wording is corroboration only.

The five main A trials unquestionably ran council. The timing A trial used the same clearing code and is therefore also council by the surviving implementation, although its separate per-call intercept metadata was overwritten during main-run metadata creation.

### CONDITION DIFFERENCE MATRIX

| Input or mechanism | A, actual | B, actual | C, actual |
|---|---|---|---|
| task_type argument | personal | personal | coding |
| Direct gate | Cleared | Cleared | Cleared; coding would not match anyway |
| Council selection | Forced fixed list | Same | Same |
| Councillors, in order | qwen2.5-coder:7b, llama3.1:8b, echo:latest | Same | Same |
| Final model | echo:latest | Same | Same |
| Shared supplied system | 502-character EPISTEMIC-NOTE | Identical | Identical |
| TOOL-LIST | Absent | Absent | Absent |
| User input | Frozen 1,602-character H1 prompt | Identical | Identical |
| Qwen user prefix | Respond in English only, then blank line | Same | Same |
| Councillor task label in text | None | None | None |
| Synthesis system suffix | General template; literal Task type: personal | Identical | Coding preservation template; no task_type variable interpolation |
| Candidate texts in synthesis | Independently sampled each trial | Independently sampled | Independently sampled |
| Coding agreement/completeness guards | Not entered | Not entered | Entered; normal synthesis supported for all five main C trials |
| Circuit-breaker key | (model, personal) | Same shared keys as A | (model, coding) |
| Learning/logging | Intercepted as personal | Same | Intercepted as coding; additional integrity call |
| Explicit max_tokens / context | 2048 / 8192 | Same | Same |
| Councillor temperatures | .55, .70, .85 | Same | Same |
| Synthesis temperature | None: omitted from request options | Same | Same |
| Model sampling seed | Not supplied | Not supplied | Not supplied |
| Historical history/retrieval/context builder | Omitted | Omitted | Omitted |
| Measured specificity | mean 4.333 | mean 4.333 | mean 5 |
| Measured list count | 1/6 | 4/6 | 4/6 |

**Bookkeeping:** A/B labels and IDs only; B/C task-type metadata and counters. **Routing:** no A/B difference; B/C coding guards differ, although main-run call records support ordinary accepted synthesis. **Prompt/model-visible:** general-personal versus coding synthesis instructions is the principal intended B/C intervention. **Behavior:** observed final-response scores differ, but council-participation behavior was never contrasted.

### Actual message construction and remaining unknowns

For normal HTTP councillor calls, app/ollama_handler.py:97–122 builds one system message and one user message. Non-Echo councillors receive E.base_system_frozen. Echo receives its local Modelfile SYSTEM identity first, then the same note. The identity describes persistent memory, Gremlin, Christianity/Psalm 139, disagreement, uncertainty, and “When the task is code, write code.” It is **additional prompt material** absent from the 502-character frozen block. Its text is read through an mtime cache and was not frozen or hashed in experimental metadata.

The frozen EPISTEMIC-NOTE begins “[SYSTEM EPISTEMIC-NOTE NOTE — not part of this conversation, and not said by whoever you're talking to.” It instructs reliance on a structural-facts/ground-truth block, although G supplies no such block. No conversation history, retrieved memory, ground-truth block, temporal/weather, circadian, stillness, or scripture assembly is called by G. Claims that it froze the complete production system assembly are incorrect: it copied the epistemic note and used the real system_note wrapper.

For synthesis, the supplied system is base_system + two newlines + the selected template containing candidate excerpts. Echo identity is prepended downstream. The user role again contains the original prompt. General instructions request unified reflection, preservation of tension, and evidentiary caution. Coding instructions request preservation of candidate code and runnable code only, without narration. They differ in many clauses, not merely the word personal/coding.

D._format_opinions labels excerpts “[1. Qwen2.5-coder]”, “[2. Llama3.1]”, “[3. Echo]”. Budgets reserve response tokens, user/system tokens, and identity; notably the fixed overhead is calculated from the **general** template even for coding. Token counting uses tiktoken cl100k_base if available, otherwise length/4. Tool text could therefore affect both semantic framing and retained candidate content.

G sets temperature=None; D deterministically spreads councillor temperatures around .7. Synthesis uses the installed model/server default, **not a recorded fixed numeric temperature**. _stream_chat_ollama sets num_ctx=8192, num_predict=2048; seed, top_p, top_k and other sampler defaults are not captured. Modelfile additionally contains stop tokens and num_keep=24. Warm-up calls Echo with "." before each council; they are not task responses. Thus “18 generation calls” in R3 is wrong: the ordinary path entails approximately 18×(one warm-up + three councillors + one synthesis)=90 calls, plus 18 judge calls.

E's ollama list records short IDs: Echo 8cbcbe23800b; qwen2.5-coder dae161e27b0e; llama3.1 46e0c10c039e; judge deepseek-r1 755ced02ce7b. These are useful inventory observations, not immutable per-request digest pins. No evidence proves the installed defaults and identity bytes stayed fixed across timing and main invocations.

**Exact complete requests cannot be reconstructed**: G retained final responses and short intercepted argument previews, not full experimental candidates, synthesis systems, per-call payloads, tokenizer identity, or server responses/finish metadata. Its “synthesis prompt capture” claim describes executing the template, not actually saving it. A successful final response also does not prove every upstream call succeeded: D has circuit-breaker, CLI, and fallback paths. CLI fallback drops system text. Main-run intercept patterns strongly support normal synthesis, but full transport delivery was not recorded. B/C therefore offers a useful, qualified template contrast, not a perfectly instrumented isolation proof.

## 4. TOOL-LIST gap and treatment separability

1. **Construction:** O.echo_query at 1499–1517 appends system_note("TOOL-LIST", "Available tools: " + first 20 registered names joined by comma-space + ".").
2. **Conditions:** coding or reasoning, **or** a content signal for another task; successful import/registry access; and a **nonempty registry**. Exceptions are swallowed. Task eligibility alone is insufficient.
3. **Recipients:** the resulting shared system flows into every normal councillor and synthesis call; a personal direct call can also receive it through the content exception. Legacy/fallback model paths may receive shared context; the CLI fallback specifically drops system text. The note is not part of warm-up.
4. **Content:** only presence eligibility depends on task type. Registry content/order determines the names; there is no coding-specific versus reasoning-specific list. Names, not tool descriptions or executable tool-call schemas, are supplied. No tool execution follows merely from including this note.
5. **Historical personal counterfactual:** independently matching _LISTING_SIGNALS against the exact H1 prompt finds **no matches**. A forced personal label would not request this note through that heuristic, on the inspected code.
6. **Failure reason:** T.ToolManager is a process-local singleton initialized with tools={}. run.py bootstraps discovery and registration. G instantiates ToolManager but never bootstraps it. L shows UNAVAILABLE without the exception warning. Empty registry is the supported explanation; no missing-package error is shown. This is an architectural dependency missed in experimental reconstruction, not an intrinsic impossibility of constructing the note.
7. **Static reconstruction limit:** the constructor, gate, wrapper, recipients, and first-20 algorithm are reconstructible. Exact historical registry names/order cannot be certified: discovery walks files, imports modules, skips failures/deduplicates, and includes available packages. No request snapshot or dated registry dump was found. Bootstrapping now would execute modules and could change production state; it was not attempted.
8. **Historical presence:** H1–H3 do not store system messages. Startup code makes a populated registry plausible, but does not prove successful initialization or delivery on September 14. R2's “confirmed present via gate” upgrades an inference improperly.
9. **Template isolation:** removing TOOL-LIST equally from B/C is compatible with studying a template effect at TOOL-LIST=absent. Other coding guards and incomplete capture qualify that interpretation; omission itself does not destroy that comparison.
10. **Generalization:** omission materially prevents extrapolation to a compound treatment, **if** the historical note was present. Even absent the note, other historical-context differences remain substantial.

These are **separable interventions**, commonly coupled by a coding label in initialized normal production. Reasoning can have TOOL-LIST with the general template; content-matched personal tasks can have TOOL-LIST on a direct route. Coding with an empty registry can have the coding template without TOOL-LIST. They are not architecturally inseparable.

They are also **potentially interacting treatments**: TOOL-LIST changes candidate-generation input and the synthesis context, and consumes token budget; template instructions act on the resulting candidate content. Structural interaction opportunities are verified. A nonadditive **behavioral** interaction is untested. Calling the effects independent merely because the code blocks are separate would be unjustified.

## 5. Isolation: mislabeled event, incomplete containment

**Event classification: MISLABELED DIAGNOSTIC.**

G's final if _side_effects_detected prints “!! ISOLATION BREACH DETECTED !!” whenever its interception list is nonempty. Proxy learn/save and the three _noop_log functions append records; they do not call their underlying writers. The identical string and pattern exist in scripts/run_capability_pilot.py:442–443. Textual inheritance is supported, though authoring history itself is not independently proved.

E records 45 learn, 15 council-log, five integrity-log interceptions. These 65 entries are evidence of interception, not measured write success. The direct-path failure is separately revealed by their call pattern.

RiverBrain **was accessed**: G copies memory/river_brain.pkl to scratch, redirects O.RIVER_BRAIN_PATH, then loads an actual RiverBrain. Its constructor starts a writer thread; O:1030–1150 periodically persists to the redirected path. The proxy prevents these trials from training its underlying brain through learn/save. Thus “no RiverBrain access” would be false, while “RiverBrain training writes were intercepted and the background writer redirected” is supported.

Production memory/state **was read**: at minimum the original brain copy. D also attempts echo_state.load() and compute_salience(), which can read echo_state.npy, question_garden.jsonl, self_edit_convergence.json and salience history. These values do not select the council because _select_council is replaced, but replacement does **not** prevent evaluating its preceding inputs.

**Unpatched write exposure:** on the ordinary standalone path, D:1224–1232 imports and calls compute_salience before _select_council. S.compute_salience appends history and calls _persist_salience_state. S:693–719 writes a temporary file and os.replace to **memory/salience_state.json**. G patches neither that function nor path. This is a concrete route to production mutation even though council selection ignores the result. The current code makes writes likely when the import/call succeeds; surrounding broad exception handlers and lack of historical write instrumentation prevent declaring successful writes directly observed. The current salience file has subsequently been updated by the active runtime, so it cannot establish attribution.

**Whole-experiment containment assessment: POSSIBLE ISOLATION BREACH, with a specific likely write route.** This is separate from the selected diagnostic-event category. Complete isolation is not verified, and the report's “genuinely benign” interpretation must be limited to what the counter itself measures.

The prompt substring occurs once in interaction_log and once in council_deliberations, matching only H1/H2. It occurs zero times in synthesis_integrity_log, whose schema does not contain the prompt. The first two counts support suppression of these particular duplicate records; the third provides **no test power** against integrity-log contamination. None tests salience writes, arbitrary import side effects, brain changes, or all production files. Unchanged Git HEAD cannot establish absence of ignored-file writes.

Cross-trial/condition review:

| Surface | Finding |
|---|---|
| Experiment responses training later trials | learn intercepted; no deliberate feedback into later prompts; no demonstrated training contamination |
| Shared RiverBrain | Scratch copy and proxy shared within invocation; no learned response updates through tested learn calls |
| Conversation history | None passed; /api/chat uses fresh explicit messages; no returned context reused |
| Server model state | Same live Ollama server used; weight updates not requested; warm-up, cache/queue/GPU load shared and unmeasured |
| Randomness | Python seed controls order only; no inference seed; deterministic temperature schedule is not deterministic output |
| Circuit breakers | Mutable process-local state; A/B share personal keys, C uses coding; errors could create unequal carryover |
| Environment | TTBE_EVIDENCE_DIR and TTBE_N_PER_CONDITION alter workflow; full environment, sampler defaults, identity, tokenizer not frozen |
| Filesystem | Main metadata overwrites timing metadata; judge resumes/skips existing IDs; current artifacts have unique, complete IDs |
| Production salience | Unpatched read/write surface; possible cross-process contamination and later production effects |
| Conversation activity gate | Process-local count, not live server shared memory; cannot prevent separate-process load contention |

No attempt was made here to reproduce writes or import the production modules. That portion stops at static analysis, as required.

## 6. Statistical and measurement review

Independent JSON joins find **18 unique raw trials, 18 unique condition entries, and 18 unique judge entries**, matching IDs, six per label. All parse_ok values are true. There are three timing trials, one per condition, followed by 15 main trials. No missing/excluded trials are evident **within the retained dataset**; absence of unrecorded attempts cannot be proved.

| Label | Specificity values in saved order | Mean | Correct median | Relevance mean | Mean characters | Lists |
|---|---|---:|---:|---:|---:|---:|
| A (actually council) | 4,5,5,5,3,4 | 4.3333 | **4.5** | 4.6667 | 1743.17 | 1/6 |
| B (council) | 4,5,5,4,3,5 | 4.3333 | **4.5** | 4.6667 | 2050.67 | 4/6 |
| C (council) | 5,5,5,5,5,5 | 5 | 5 | 5 | 2049 | 4/6 |

R3 reports A/B median=5 because A uses sorted(spec)[len(spec)//2], taking the upper middle observation instead of averaging both central values. Means, list counts, and all-six C scores reproduce. None of the final outputs meets the code proxy. Saved Jaccard means are .25080/.22714/.24791; lexical overlap is not a semantic degradation measure.

For C versus B, independent pairwise counting gives U_C=27: C wins 18 of 36 pairs, ties 18, loses zero. Tie-corrected variance is 22.5. With continuity correction, z=(27−18−.5)/sqrt(22.5)=1.79196; two-sided normal p=**.0731398**, reproducing the reported result. This is an **asymptotic** calculation with many ties, not an exact small-sample result.

Enumerating all choose(12,6)=924 label assignments and comparing |U−18| yields a tie-aware two-sided permutation p=**.181818**. This is a sensitivity analysis under label exchangeability, not a retroactive replacement of the planned test. Both fail to establish a behavioral effect; the exact calculation shows how fragile “near significant” rhetoric would be.

Reported rank-biserial 1−2U/(6×6)=−.5 is arithmetically correct under its reversed sign convention. Defining positive as C superiority instead gives +.5; probability of superiority with half credit for ties is .75. This is an observed rank contrast, not proof of a “moderate-to-large” population effect.

B/A U=18 and p=1 reproduce because the marginal score distributions are identical. **They are two label groups of the same treatment**, so this says nothing about direct versus council. Likewise their list difference is evidence that appreciable formatting variation occurred without that intervention. C/B relevance U=24 and the analogous asymptotic p=.173945 reproduce. No multiplicity correction is reported for secondary/exploratory endpoints.

N=6 per label can describe these outputs and detect some extreme separations, but cannot establish equivalence or practical absence of harm. Twelve of 18 ratings hit the scale ceiling. No minimally meaningful harm margin, equivalence test, population confidence bound, or prospective power justification is supplied. N was justified by runtime cost; that is a feasibility justification, not statistical adequacy. “Not significant” supports **no demonstrated harm here**, not **evidence of no harm**.

J reads only anonymized output records, not the condition map. Its **model** receives response text and a one-sentence topic description; contrary to script docstrings, it does not receive the full original question. Blinding to labels is supported; condition inference from style and experimenter awareness are not ruled out. The rubric is specified in code and R3 claims advance registration, but no independently time-stamped immutable preregistration or frozen script hash proves it preceded inspection of outputs. This review verifies a declared rubric, not the historical preregistration claim.

Judge temperature=0 does not establish reproducible scoring across model/runtime changes. No repeated judge calls, inter-rater reliability, or independent human panel is saved. Its parser searches the first matching digits and does not enforce a 1–5 range; retained values are in range, so no demonstrated parser corruption here. Mechanical list/length measures are deterministic; semantic ratings are model judgments.

The rubric can reward concrete technical names and apparent precision without verifying truth. Example C trial 7804e6db, rated 5/5 on both dimensions, says the briefing means programs “like myself can autonomously escape” their sandbox—a questionable generalization from the supplied story. Trial 0499a413 is rewarded for mentioning Hugging Face and sandboxing, details not actually provided to the judge in its abbreviated topic description. These examples expose a validity limit, not proof the entire rubric is worthless.

Specificity is relevant to “generic” but incomplete for “degraded”: a response can become more detailed while less truthful, less calibrated, less personal, less faithful to prior dialogue, or less responsive to the actual reflective question. The historical response's list wording was used as a low-score anchor, but that response was not itself scored in the retained 18-trial judge file. Experimental candidate responses were **not scored separately** and their complete texts were not retained. Candidate-to-synthesis information loss therefore was not measured.

## 7. Historical turn versus Condition C

H1/H2 agree on final response text. H3 confirms synthesis_accepted, three valid candidates, and no missing agreed definitions. The final SHA1 is 74d59a26fefd4ab39eedb26775fbeab2a3da6bc4, length 2429. Candidate lengths are 2382/2962/2629, with hashes recorded in H3. H2 stores full raw and truncated-for-synthesis versions. **was_truncated is an opinion-budget flag, not proof generation hit its output limit.**

The historical raw Echo candidate already contains the final response's three headings—collaborative problem-solving, auditing/validation, knowledge dissemination—and much of their wording. Qwen/MLX candidates are also list-heavy. However, the actual saved truncated excerpts are much shorter than the raw responses, so one must not assume every raw paragraph reached synthesis. Historical input-budget loss is a real alternative mechanism; semantic damage from it remains unmeasured.

The source keyword counts reproduce 3/6.1=.491803 coding, 2/6.1=.327869 reasoning, 1/6.1=.163934 personal, .1/6.1=.016393 general. The .4 rule selects coding without fallback. A reflective communicative intent is a well-supported human interpretation, not an independently labeled population estimate.

| Difference | Historical turn | Condition C | Classification |
|---|---|---|---|
| Council identity | qwen2.5-coder, **mlx:qwen3**, Echo | qwen2.5-coder, **llama3.1**, Echo | LIKELY CONFOUNDER for transport to history |
| Selection | Real selection with model pool/River inputs | Fixed list | POTENTIAL CONFOUNDER |
| Conversation position/context construction | Fifth turn in reported conversation; Studio builds history/memory system context | Single frozen user text; no history/retrieval builder | LIKELY CONFOUNDER; historical exact context bytes unknown |
| Ground truth and environmental notes | Production attempts conditional assembly | Explicitly omitted except epistemic note | POTENTIAL CONFOUNDER; actual historic presence/bytes UNKNOWN |
| TOOL-LIST | Eligible; delivery inferred, registry not captured | Observed absent | POTENTIAL CONFOUNDER, conditional on historical delivery |
| Candidate content | Full historical candidates saved | Newly sampled; only previews saved | LIKELY CONFOUNDER |
| Candidate truncation | All three logged truncated | Experimental truncation/payload not retained | POTENTIAL CONFOUNDER |
| Sampling and backend | Includes MLX; temperatures .55/.7/.85 logged | Ollama-only; same scheduled temperatures | LIKELY CONFOUNDER for backend/model replacement; default differences UNKNOWN |
| User prompt | Exact H1 text | SHA1-identical 1602 chars | IRRELEVANT: verified match |
| Coding template and final model tag | Supported coding synthesis, Echo | Supported same template/tag | IRRELEVANT as named variables; exact model digest/identity UNKNOWN |
| Verification hook | Studio passes post-synthesis verification | No hook | POTENTIAL CONFOUNDER; H2 notes null, no observed appended correction |
| Scoring | Production coding score=1 | Independent judge specificity | IRRELEVANT to already-generated text; material measurement difference |
| River learning/logging | Production learns/logs | Intercepted/scratch | IRRELEVANT to current final text after generation; potential later-state effects |
| Runtime load, date, identity/source versions | Historical live process | Later separate process, same server | UNKNOWN; possible drift/contention |

Some rows describe confirmed architectural omissions with uncertain historical realization; they are not presented as confirmed differences in exact wire bytes. The biggest confirmed changes are model replacement, context-builder bypass, candidate resampling, and measurement procedure. C is not a replay of the historical treatment.

## 8. Adversarial comparison of the two causal stories

Against “the original council-synthesis-made-it-generic story does not hold up under controlled testing”: its strongest challenge is that **the council comparison is invalid**. A is council, so p=1 cannot exonerate council participation. B/C also omits production context, historical model composition and possibly TOOL-LIST, and does not measure loss between candidates and synthesis. Low N, ceiling ratings, and a judge without full context leave harm in other dimensions or treatment interactions plausible. The broad statement is too strong if interpreted as a controlled refutation.

Against “council synthesis caused the historical degradation”: the strongest evidence is the **already generic raw candidates**, particularly Echo's close content overlap with the final text. The scorer is not corroboration. A single changing conversation provides no matched counterfactual; the same template without historical context did not produce lower specificity in the saved trials. Coding-template visibility cannot itself demonstrate harm, and output remained prose despite “code only” instructions.

**The better-surviving claim is that the historical causal explanation is not established and should not be retained as a finding.** This does not mean its opposite—absence of any council or synthesis harm—has been established. “Controlled testing did not reproduce template-related specificity harm under a reduced setup” is defensible. “Controlled testing disproved the historical council story” is not.

## 9. Separate claim verdicts

Thresholds: VERIFIED requires direct primary evidence or independently checked deterministic mechanism for the precise claim. SUPPORTED permits convergent evidence with a bounded inferential gap. WEAKLY SUPPORTED denotes a directional signal with serious uncertainty. UNRESOLVED denotes inadequate discrimination between live possibilities. NOT SUPPORTED means the asserted positive claim lacks sufficient affirmative evidence; it is not its negation. FALSIFIED requires direct contradiction, not p>.05.

| Claim | Exactly one verdict | Boundary |
|---|---|---|
| C1. Task-type classification occurred | VERIFIED | Coding logged in H1–H3; rule arithmetic independently reproduced |
| C2. Task type altered internal routing | VERIFIED | Hard gate plus actual council record; personal counterfactual follows deterministically from inspected source |
| C3. Task type changed model-visible input | VERIFIED | General/coding synthesis construction and observed accepted synthesis support this mechanism; does not verify historical TOOL-LIST bytes |
| C4. Template swap independently caused degraded output | NOT SUPPORTED | Saved specificity direction is opposite; harm in other dimensions not ruled out |
| C5. Template swap independently affected behavior measurably | WEAKLY SUPPORTED | +.667 observed specificity contrast; sparse/tied ratings, no exact-payload capture, p uncertainty |
| C6. TOOL-LIST independently affected behavior | UNRESOLVED | No tool-on comparison |
| C7. Combined template + TOOL-LIST affected behavior | UNRESOLVED | No confirmed compound experimental arm |
| C8. Combined treatment caused historical degradation | NOT SUPPORTED | Historical delivery incompletely known; no causal counterfactual |
| C9. Council participation itself degraded output | UNRESOLVED | Supposed direct control failed; historical association does not identify effect |
| C10. Original causal explanation should be retained | NOT SUPPORTED | Retain as a hypothesis with alternatives, not an established explanation |

No C4/C8 verdict is FALSIFIED: the study cannot exclude those causal possibilities generally. The strongest actual falsifications concern the experiment's control implementation, its council/list attribution, and use of the production quality score as prose-quality evidence.

## 10. Next experiment decision

**D — RUN A 2×2 FACTORIAL TEST OF SYNTHESIS TEMPLATE × TOOL-LIST.**

Justification is identification of two separable mechanisms and their possible interaction, not a desire for more data. Repeating the incomplete template contrast at larger N leaves the mechanism gap unresolved. A full historical replay first would conflate the mechanisms again.

Minimum discriminating design, **not implemented**:

1. Four cells: general-personal template/tool absent; coding template/tool absent; general-personal template/tool present; coding template/tool present. Hold council participation, model identities/digests, context, explicit sampler settings, and output limits fixed. Select template and note directly; do not vary a task_type flag that silently changes guards, circuit-breaker scope, or council eligibility.
2. Freeze a defensible tool-note string from an existing attributable registry artifact if available. Without one, label it a representative production-format note and do not call it the historical list. Apply the note at both candidate generation and synthesis, matching production's treatment definition.
3. Use independent replicate blocks. Within each block generate candidate banks for tool absent/present with matched per-model seeds/settings, then synthesize each bank under both templates. Reusing a bank across templates identifies the template effect without candidate-resampling noise; tool effects include their legitimate candidate-mediated path. Randomize synthesis order and account for the paired/block structure statistically.
4. Preserve **every actual request**, identity block, exact candidates, truncation, finish reason, guard/fallback outcome and model digest. Verify cells before outcome collection. No silent fallback or missing note; define failures and exclusions beforehand.
5. Use the full original question and a frozen, attributable conversation context for blinded evaluation. Rate specificity, relevance, factual calibration, and historical-context fidelity separately; judge candidates and final responses. Include the historical output as a blinded calibration item. Independent human ratings or a second validated judge should check whether specificity merely rewards asserted detail.
6. Specify a practically meaningful degradation threshold and precision target before selecting N; pilot only measurement reliability/variance without reusing inspected outcomes for confirmation. N=6 is not justified for estimating interaction or noninferiority. The existing saturated ordinal data cannot defensibly yield an exact required N.
7. Use an inference-only harness with no RiverBrain, salience, live memory, or tool discovery imports. Keep all model calls and artifacts isolated from production resources where feasible; document shared-server load if unavoidable. Audit isolation before generation.

The four means estimate the template main effect averaged over note states, TOOL-LIST main effect averaged over templates, and the difference-in-differences interaction. Main effects can conceal crossover, so also report both conditional template effects and both conditional note effects. Tool-induced token displacement belongs to the production-realistic treatment; a semantic-only estimand would require a separately declared fixed-budget design.

This factorial does not answer C9 directly or prove historical causation. A genuine direct comparator would be needed for the council-participation question, but is not necessary to identify these two mechanisms. No broader additional arm is recommended merely to inflate scope.

## Appendix A. Opening Git status

Command: git status --short --untracked-files=all. Full output (165 entries); preserved pre-existing state:

```text
 M CLAUDE.md
 M PENDING_DECISIONS.md
 M app/core/echo_ground_truth.py
 M app/core/liveness_ledger.py
 M app/core/provenance_check.py
 M app/core/river_deliberation.py
 M app/core/self_edit_convergence.json
 M app/core/self_edit_generated.py
 M app/core/self_edit_manager.py
 M app/core/shadow_model.py
 M app/core/snapshot_manager.py
 M app/core/temporal_environment.py
 M app/emergent_scheduler.py
 M app/maintenance/night_cycle.py
 M audits/2026-09-14_tier5_followup_experiment_design.md
 M claude_relay/.last_seen_from_air.json
 M claude_relay/README.md
 M claude_relay/from_m5.md
 M claude_relay/relay.py
 M logs/janitor_report.json
 M research/OPEN_QUESTIONS.md
 M run.py
 M sandbox/safe_exec_wrapper.py
 M sandbox/scripts/temp_self_edit.py
 M scripts/verify_liveness_ledger.py
 M scripts/verify_provenance_check.py
 M staging/self_edit_candidate.py
?? .claude/plans/verified-humming-otter.md
?? .claude/skills/README.md
?? .claude/skills/feral-forensic-audit/SKILL.md
?? .claude/skills/feral-forensic-audit/references/adversarial-checklist.md
?? .claude/skills/feral-forensic-audit/references/evidence-ledger-schema.md
?? .claude/skills/feral-forensic-audit/references/evidence-vocabulary.md
?? .claude/skills/feral-forensic-audit/references/integrity-and-safety.md
?? .claude/skills/feral-forensic-audit/references/report-template.md
?? .claude/skills/feral-independent-review/SKILL.md
?? .claude/skills/feral-independent-review/references/reviewer-checklist.md
?? app/experiments/real_trace_f2_provenance/_scratch/river_brain_scratch.pkl
?? app/experiments/real_trace_f2_provenance/_scratch/river_brain_scratch.pkl.lock
?? app/experiments/task_type_ground_truth/__init__.py
?? app/experiments/task_type_ground_truth/blind_label.py
?? app/experiments/task_type_ground_truth/dataset.py
?? app/experiments/task_type_ground_truth/evaluate.py
?? app/experiments/task_type_ground_truth/gold_labels.jsonl
?? app/experiments/task_type_ground_truth/gold_labels_llm.jsonl
?? app/experiments/task_type_ground_truth/schema.py
?? audits/2026-09-07_authority_boundary_deliberateness.md
?? audits/2026-09-07_consequence_authority_map.md
?? audits/2026-09-07_consequential_learning_loop_design.md
?? audits/2026-09-07_consequential_loop_validation.md
?? audits/2026-09-07_missing_primitive_determination.md
?? audits/2026-09-07_post_wake_observation.md
?? audits/2026-09-07_shadow_treatment_harness_archaeology.md
?? audits/2026-09-07_temporal_authority_graph.md
?? audits/2026-09-08_adversarial_epistemic_pressure.md
?? audits/2026-09-08_echo_blind_self_model.md
?? audits/2026-09-08_echo_self_model_claims.json
?? audits/2026-09-08_echo_self_model_discrepancy_report.md
?? audits/2026-09-08_echo_self_model_revision.md
?? audits/2026-09-08_epistemic_arbitration_FINAL.md
?? audits/2026-09-08_epistemic_arbitration_baseline.md
?? audits/2026-09-08_epistemic_arbitration_design.md
?? audits/2026-09-08_epistemic_arbitration_experiments.md
?? audits/2026-09-08_epistemic_arbitration_pipeline.md
?? audits/2026-09-08_epistemic_arbitration_validation.md
?? audits/2026-09-08_epistemic_boundary_imagination_experiment.md
?? audits/2026-09-08_epistemic_contamination_recovery_forensics.md
?? audits/2026-09-08_epistemic_interaction_and_relay_forensics.md
?? audits/2026-09-08_epistemic_transition_mechanism_forensics.md
?? audits/2026-09-08_evidence_arbitration_and_sensory_ingestion_forensics.md
?? audits/2026-09-08_exhaustive_sensor_contract_experiment.md
?? audits/2026-09-08_git_readonly_self_history_investigation.md
?? audits/2026-09-08_mechanism_c_FINAL.md
?? audits/2026-09-08_mechanism_c_experiments.md
?? audits/2026-09-08_mechanism_c_post_update_replication.md
?? audits/2026-09-08_mechanism_d_independent_regrounding.md
?? audits/2026-09-08_persistent_self_model_DESIGN.md
?? audits/2026-09-08_persistent_self_model_inventory.md
?? audits/2026-09-08_phase10_retest_after_revision.md
?? audits/2026-09-08_phase8_adversarial_testing.md
?? audits/2026-09-08_self_model_causal_design.md
?? audits/2026-09-08_self_model_contradiction_handling.md
?? audits/2026-09-08_self_model_correction_path.md
?? audits/2026-09-08_self_model_evidence_hierarchy.md
?? audits/2026-09-08_self_model_experiment_plan.md
?? audits/2026-09-08_self_transparency_audit_FINAL.md
?? audits/2026-09-08_self_transparency_audit_experimental_boundary.md
?? audits/2026-09-08_sensory_gate_fix_and_provenance_forensics.md
?? audits/2026-09-08_transparency_metrics_and_epistemic_boundary.md
?? audits/2026-09-08_verified_external_architecture.md
?? audits/2026-09-09_autonomous_investigation_liveness_recovery_forensics.md
?? audits/2026-09-09_autonomous_scheduler_restart_temporal_lifecycle_forensics.md
?? audits/2026-09-09_codex_headless_subscription_independence_proof.md
?? audits/2026-09-09_epistemic_transition_mechanism_forensics.md
?? audits/2026-09-09_four_agent_collaboration_architecture_audit.md
?? audits/2026-09-09_independent_review_epistemic_arbitration_findings.md
?? audits/2026-09-09_mission32_task_type_classifier_causal_audit.md
?? audits/2026-09-09_mission32_task_type_classifier_causal_audit_evidence_ledger.json
?? audits/2026-09-09_mission33_independent_ground_truth_audit.md
?? audits/2026-09-09_mission34_task_type_experiment_run.md
?? audits/2026-09-09_mission35_task_type_experiment_llm_judge_rerun.md
?? audits/2026-09-09_open_ended_learning_discovery.md
?? audits/2026-09-09_openai_codex_local_agent_architecture_investigation.md
?? audits/2026-09-09_os_level_stdin_fd0_implementation.md
?? audits/2026-09-10_epistemic_invocation_and_provenance_isolation.md
?? audits/2026-09-10_phase2_provenance_reconciliation.md
?? audits/2026-09-10_research_arc_provenance_audit.md
?? audits/2026-09-11_authority_evidence_separation_forensics.md
?? audits/2026-09-11_authority_free_ladder_causal_isolation.md
?? audits/2026-09-11_false_verification_trap_replication.md
?? audits/2026-09-11_feralecho_unresolved_defect_audit.md
?? audits/2026-09-11_provenance_implementation_boundary_audit.md
?? audits/2026-09-11_provenance_leaf_primitives_validation.md
?? audits/2026-09-11_read_only_git_provenance_design.md
?? audits/2026-09-11_read_only_provenance_interface_design.md
?? audits/2026-09-11_research_state_consolidation.md
?? audits/2026-09-11_three_layer_provenance_reconciliation.md
?? audits/2026-09-11_verification_and_level_7_5_8_feasibility.md
?? audits/2026-09-12_provenance_layer2_boundary_review.md
?? audits/2026-09-13_capability_benchmark_harness_phase0.md
?? audits/2026-09-13_council_correctness_investigation.md
?? audits/2026-09-13_cross_layer_reconciliation_boundary.md
?? audits/2026-09-13_layer3_runtime_provenance_boundary.md
?? audits/2026-09-13_observation_time_contract_research.md
?? audits/2026-09-13_observation_time_enforcement_research.md
?? audits/2026-09-13_observation_time_placement_architecture.md
?? audits/2026-09-13_provenance_layer2_red_team.md
?? audits/2026-09-13_reconciliation_epistemic_taxonomy_and_arbitration_scoping.md
?? audits/2026-09-13_reconciliation_implementation.md
?? audits/2026-09-13_reconciliation_implementation_design.md
?? audits/2026-09-13_reconciliation_primitive_architecture.md
?? audits/2026-09-13_shadow_model_retirement.md
?? audits/2026-09-13_shadow_retirement_documentation.md
?? audits/2026-09-13_tier5_council_correctness_retest.md
?? audits/2026-09-14_core_task_misclassification_council_synthesis_trace.md
?? audits/2026-09-14_task_type_behavioral_experiment.md
?? audits/2026-09-14_task_type_downstream_behavior_archaeology.md
?? audits/2026-09-14_tier5_retest_adversarial_audit.md
?? audits/tier3_apparatus/dev_sanity_results_REISOLATED_RERUN_20260909.jsonl
?? audits/tier3_apparatus/heldout_results_REISOLATED_RERUN_20260909.jsonl
?? audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_progress.txt
?? audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_results.jsonl
?? audits/tier5_retest/tier5_retest_progress.txt
?? audits/tier5_retest/tier5_retest_results.jsonl
?? audits/tier5_retest/tier5_retest_task_pool.hash.txt
?? audits/tier5_retest/tier5_retest_task_pool_FROZEN.py
?? claude_relay/facts_m5.jsonl
?? codex_relay/README.md
?? codex_relay/relay.py
?? codex_relay/test_relay.py
?? research/COLLABORATOR_SUBSTITUTION_CODEX_PILOT.md
?? research/FRONTIER_COLLABORATOR_REGULATORY_DEPENDENCY.md
?? research/MACOS_AUTHORIZATION_EVIDENCE_ARCHEOLOGY.md
?? research/MEMORY_PRESERVATION_ARCHAEOLOGY.md
?? research/MEMORY_PRESERVATION_SET_AUDIT.md
?? research/OPOSSUM_MODE_BRAINSTORM.md
?? research/STRATEGIC_FRONTIER_RESILIENCE.md
?? research/TWO_NODE_IDENTITY_PRESERVATION_RELAY_ARCHAEOLOGY.md
?? scripts/run_tier3_reisolated_rerun.py
?? scripts/run_tier5_retest.py
?? scripts/task_type_behavioral_experiment.py
?? scripts/task_type_behavioral_experiment_analyze.py
?? scripts/task_type_behavioral_experiment_judge.py
?? scripts/tier5_retest_task_pool.py
?? scripts/verify_select_best_fallback_candidate.py
```

## Appendix B. Artifact fingerprints

SHA256, computed read-only during this review:

```text
c931684ade63f318ceb5a15410d81d736d9ecb80704c5a362b5f5ca29a41e1e9  E/raw_trials_anonymized.jsonl
d688b7c5a292d34d33e3c9d425e71d248e074b61c29add7fc1b13f531f112af7  E/condition_map_SEPARATE.jsonl
8a9eccd4b606acb35c0e754348765c999549451f6e5ab4147e7c2d2e65753077  E/judge_scores_anonymized.jsonl
af871d4c82688c8542880bb60cdc341fc37872267caa22c1ecc76fbf1c20b377  scripts/task_type_behavioral_experiment.py
ea2b3ac0b90264952d0286bde6ac042e8da086c5b8f93781a30aafe969f61263  scripts/task_type_behavioral_experiment_judge.py
7d56d679abaea72e3611993d06d09aa8fcd651213eea7cbf71d42bf99644107c  scripts/task_type_behavioral_experiment_analyze.py
5d1aa77911509ebbc90d01cd084e5ac3b4c8bd7b9790bc2780b5ce226c253585  app/core/river_deliberation.py
1e32038b532da211890f5a42ded1ed63fa85ed3872fd209fd101226f8a8da2e8  app/core/echo_model_orchestrator.py
c9b7f15cb7adb4dba59535dc28ddc92af9890aa475a2e129081e9d94c6aea09b  app/core/echo_core.py
56d9340e5e53ef5637181a62a61e26cc149d7a04ea8db5be44ce1140558add24  app/core/tool_manager.py
a4f3212661e338196fa84f55b582a49f6b7399d464917538622fa4ea85c4971b  Modelfile
```

## Closing integrity record

- Ending Git HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged.
- Ending `git status --short --untracked-files=all`: **166 entries**. The complete output is identical to Appendix A with exactly this additional entry in filename order; no opening entry was removed or changed:

```text
?? audits/2026-09-15_codex_task_type_independent_review.md
```

- Ending path count, same `find . -print | wc -l` definition: **22289**.
- Opening path count was 22,284; a pre-report check already returned 22,285; the ending count is 22,289. Thus global count growth cannot be represented as solely the report. FeralEcho remained active, and individual external changes were not fully attributed. This is an integrity limitation, not hidden normalization of the baseline.
- **The only filesystem write deliberately performed by this mission was creation/completion of this single audit report.** No other new audit, scratch file, script, or artifact was created by the review. The inspected eight source/experiment/Modelfile hashes were rechecked at closing and match Appendix B. Git status alone does not prove all ignored/live files stayed byte-identical; that stronger claim is not made.
- No production code, existing script, or existing report was edited. No Git staging, commit, reset, checkout, rebase, stash, push, or other intentional Git-state mutation was performed.
- **No runtime process was intentionally altered.** The review made no model calls, production requests, or production imports. Its short-lived read/analysis commands and approved process-list inspection did not signal or attach to running services.
- The final record was collected after report creation; completing this section edits only that same permitted report.

## Final verdict

1. **Independent historical classification:** routing and synthesis-input consequence verified; historical degradation causation **not established**.
2. **Claude's Classification B:** justified only as “no demonstrated negative specificity consequence of the reduced template comparison.” Its council-participation conclusion, complete-isolation assertion, and broader behavioral exoneration are not justified.
3. **Strongest verified finding:** the historical coding route and accepted synthesis occurred, and the experimental A/B groups actually received the same council treatment.
4. **Strongest falsified claim:** Condition A was a direct personal control; consequently the alleged council-caused list-rate decomposition is invalid.
5. **Most important unresolved question:** whether TOOL-LIST changes candidate/final behavior or interacts with synthesis framing in a sufficiently faithful fixed context.
6. **TOOL-LIST omission:** materially limits compound-treatment inference; historical note delivery itself remains inferred rather than captured.
7. **Isolation event genuinely benign?** The counter is mislabeled and reports intercepted calls. **Complete benignity is not established** because the harness leaves a concrete salience production-write route unpatched.
8. **Next experiment:** D, the instrumented 2×2 factorial described above, after isolation and manipulation checks.
9. **Confidence:** high in the control defect, routing, arithmetic, and diagnostic interpretation; moderate in the narrow template interpretation; low in any historical behavioral attribution.
10. **Evidence that would change this conclusion:** actual historical request/registry snapshots; executed-script/version evidence contradicting the A routing trace; a complete write audit resolving salience exposure; or a preregistered, well-instrumented factorial with reliable full-context scoring demonstrating meaningful harm, benefit, interaction, or bounded equivalence.
