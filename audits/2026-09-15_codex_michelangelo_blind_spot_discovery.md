# MICHELANGELO MODE — Codex capability blind-spot discovery

Independent architectural investigation, 2026-09-15. Repository: /Users/richietate/Desktop/FeralEcho.

**Finding:** the main obstacle is not inability to search, read code, compute, or inspect a process. Existing capabilities answered several difficult questions once I chose the right environment and evidence. Reliability falls at specific transitions: current file → loaded implementation, assembled context → actual model request, attempt outcome → adaptive update, and diagnostic result → claimed capability. Some transitions lack retained evidence; others already have evidence but misleading scope or labels. No new tool is proposed.

This report completes the supplied Phases 0–3. It does not implement, repair, redesign, or recommend a tool inventory.

## Independence and method

I did not search for or read another agent's report answering this blind-spot/tool-design question. I avoided report-content searches across audits/, research/, CLAUDE.md and the agent skill directories. Directory names and opening Git status necessarily exposed filenames; those were not used as recommendations.

Production source comments incidentally referred to earlier provenance designs and a planned “four primitives” vocabulary. I treated those passages as **design-history exposure**, not independent discovery or an inventory to reproduce. I inspected and tested existing implementations on their behavior. I did not open the cited design reports or adopt their proposed remaining primitives.

This conversation already contained a previous Codex task-type experiment review and an interrupted Codex-relay check. That is prior familiarity, not a clean-slate blind review. The task-type evidence reused here is explicitly identified as a familiar case, rechecked against primary artifacts. The memory-filter fixture, interpreter mismatch, existing provenance-reader exercise, retrieval-hash recovery, windowed self-model count reconciliation, and attempt-to-learning linkage checks were performed in this mission.

Questions were selected across epistemic domains, not to maximize a proposed tool list. This is a purposive sample, not an exhaustive capability census. An unsuccessful search is not proof that no useful artifact exists anywhere.

Labels: **observed** means read from an identified artifact or returned by an actual check; **verified** means the narrow claim is supported by primary evidence plus a direct check; **inferred** means assumptions bridge an unobserved transition; **unknown** means evidence was insufficient. An observation of a self-report is not verification of its underlying claim.

## Phase 0 — Observation boundary

### Opening state

The first command recorded:

- HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce`.
- Git status: 27 modified tracked files plus the pre-existing untracked entries reproduced in Appendix A. Git was used with `--no-optional-locks`.
- Path count: **22,292**, from `find . -print | wc -l`; includes directories, ignored paths, .git, and the root.
- Repository disk usage: **1.6G**, from `du -sh .`.
- No top-level tests/ directory was found; actual verification scripts and app/experiments exist. This was a navigation correction, not evidence of absent testing.
- Initial shell `ps` failed with “operation not permitted.” A separately approved read-only process listing succeeded.

Relevant process observations at about 11:12 UTC / 04:12 Pacific:

| PID | Observed command / role | Start evidence |
|---|---|---|
| 7636 | /bin/zsh .../start_echo.sh | Sep 10, 22:41:53 Pacific |
| 7644 | python -u run.py | Sep 10, 22:41:53 Pacific |
| 87918 | python -m echo_studio.main | Sep 14, 10:47:43 Pacific |
| 13534 | Ollama serve | Sep 2, 16:10:09 Pacific |
| 97220 | Ollama llama-server, 8192 context, one parallel slot | Sep 15, 04:12:26 Pacific |

These observations show processes, not which Python modules or functions are loaded. The matching ps/rg inspection commands were excluded from the runtime interpretation.

A later successful existing provenance-reader call supplied stronger process facts for PID 7644: executable /Users/richietate/miniforge3/envs/feral_echo/bin/python3.12; cwd /Users/richietate/Desktop/FeralEcho; OS creation time 2026-09-11T05:41:53.357916+00:00. The PID file and sentinel both named 7644. Sentinel start_utc was 05:41:57.788028Z, 4.430112 seconds later, consistent with an application startup marker following OS process creation. The sentinel heartbeat advanced during this mission.

High-level shape, computed with read-only os.walk/stat (logical bytes, unlike du allocated space):

| Area | Files observed | Approximate logical bytes | Investigative implication |
|---|---:|---:|---|
| sandbox/ | 16,535 | 26.9 MB | Artifact-heavy; path count greatly overstates core-code size |
| app/ | 956 | 10.2 MB | Runtime components, experiments, backups, and bytecode mixed |
| memory/ | 348 | 1.24 GB | Largest evidence/state store; live and changing |
| audits/ | 323 | 9.4 MB | Not used as a source of blind-spot recommendations |
| scripts/ | 59 | 1.4 MB | Verification/experiment entry points, not automatically safe to execute |
| staging/ | 149 | 58.5 KB | Generated candidates and remnants |
| .git/ | 177 | 38.0 MB | Useful committed history; incomplete identity for dirty/untracked work |

### WHAT CODEX CAN CURRENTLY OBSERVE

These capabilities were exercised, not inferred from names:

| Capability | Actual check | Result and limit |
|---|---|---|
| Read repository source/artifacts | rg, bounded reads, AST parsing, JSON joins | Succeeded; large broad outputs can truncate, so focused follow-ups matter |
| Inspect Git history without changing it | log/show/diff, blob extraction and SHA256 | Succeeded; committed chronology and current-vs-HEAD difference recoverable |
| Run pure static logic without importing its application | Extracted two existing conversation-service functions through AST; synthetic search callback | Passed a concrete filtering fixture; not a live retrieval test |
| Use existing file-identity primitive | working_tree_file_identity on tracked, untracked, absent, out-of-root inputs | Succeeded under project Python; accurate disaggregated results |
| Inspect OS process identity | Approved ps; then existing psutil-based primitive in project Python | PID/cwd/executable/start time observed without attach or signals |
| Read process self-report and compare witnesses | Existing runtime_process_identity_and_self_report and reconciliation | Four agreeing relationships, **one** independent corroboration, not four witnesses |
| Check an inspected HTTP route | GET http://127.0.0.1:5000/health | Sandboxed curl failed; approved request returned {"node":"m5","status":"ok"} |
| Recover one historical retrieval item | Join trace to retrieval_provenance, match 12-hex SHA1 in current memory metadata | One matching retained 768-character record found |
| Recompute artifact summaries | JSON counts, distributions, windowed statistics | Succeeded without model calls or production state loading |

The health response is especially narrow: run.py:840–843 returns a constant JSON object. It demonstrates a responding HTTP endpoint, not council, memory, or learning health.

The default `python3` is not interchangeable with FeralEcho's interpreter. Importing the otherwise read-only provenance module failed because Python 3.13 attempted to load an x86_64 psutil extension on arm64. Using the **already installed** feral_echo Python resolved it, without installation or configuration changes. That failure is an environment mismatch, not absence of an inspection primitive. Also, shell ps being denied did not predict whether the existing psutil reader would succeed; the latter was tested and did succeed in the normal tool environment.

### WHAT CODEX CANNOT CURRENTLY OBSERVE

Within the exercised evidence and this mission's authority:

- Which exact current source bytes correspond to an already-loaded function in PID 7644. Neither its command line, cwd, nor heartbeat supplies loaded-code identity.
- Exact historical HTTP request payloads, full system context, model digest, all sampler defaults, and tokenizer/truncation decisions for the selected turn.
- The complete historical ToolManager registry or process-local session history from the observed logs.
- An atomic, simultaneous view across independent live JSON, JSONL, pickle, and in-memory objects. Individual readable files are not a global snapshot.
- An exact per-attempt RiverBrain update/persist receipt or causal contribution from aggregate counters alone.
- A counterfactual behavioral result without performing an intervention. This mission does not authorize new inference experiments or state-changing tests.
- Arbitrary production function execution as a harmless form of observation. Several “read,” “test,” and “dry_run” paths have persistent side effects.
- Missing historical bytes simply by using more search. A retained hash can identify surviving bytes, but cannot reconstruct absent bytes.

These are bounded findings. I did not test every endpoint, every installed connector, or remote peer. This mission did not continue the interrupted relay probe.

## Phase 1 — Architecture reconstructed from primary evidence

| System / claim | How I know | Evidence boundary |
|---|---|---|
| Studio receives a user turn through /chat/stream and creates a trace ID | run.py:738–742 delegates; app/routes_echo_studio.py:158–189 constructs request state | Current implementation, plus a retained real trace; not proof every historical interface used it |
| User text is separate from history/memory system context | routes_echo_studio._build_full_prompt; conversation_service.build_context_system_note | Construction verified; exact historical full system string not saved |
| Full-mode SSE can be presentation chunks of a completed answer | routes_echo_studio.py:305–316 calls echo_query before _chunk_text | A typing animation is not evidence of token-by-token inference progress |
| Dispatch can precede the fast/full branch | routes_echo_studio.py:191–196 and 285–306 | Its docstring says fast mode skips dispatch, but the actual dispatch gate precedes mode selection; no live dispatch test performed |
| Personal-like task types normally bypass council; others enter deliberation | river_deliberation.py:295–303,1162 onward | Source branch verified; content-triggered dispatch can bypass this broader path entirely |
| Council selection uses observation coverage, model/task scores, exploration and a guaranteed Echo seat | _select_council at river_deliberation.py:533, read as executable AST | Not merely “pick the highest three”; current selection still depends on live model pool/state/randomness |
| Models are called through an Ollama handler, with an MLX branch for mlx:* | river_deliberation._ollama_query; app/ollama_handler.stream_query_ollama | Transport and fallbacks inspected; no new inference invoked |
| Synthesis includes candidate excerpts in a system message and uses Echo | river_deliberation.py:1357–1421; real council/integrity trace | Exact candidate cutoffs are partly logged; actual request delivery not packet-captured |
| Tool awareness and tool execution are distinct | ToolManager stores names/functions; echo_query appends TOOL-LIST; echo_tool_dispatch supplies explicit schemas and _execute_tool branches | A listed function name is not proof it is exposed through the dispatcher or currently callable |
| Dispatcher tools include read_file, search_memory, log_thought | echo_tool_dispatch.py:302–313 and schema construction | Existing implementation, not a recommended inventory; log_thought writes a separate thought log |
| Pre-execution directory context is another tool surface | routes_echo_studio._build_full_prompt calls echo_tool_context based on listing signals | Separate from model-directed dispatch and TOOL-LIST |
| Semantic memory uses embeddings plus FAISS and JSON metadata | memory_bridge module initialization and retrieve_relevant_memories; app/lib/vector_memory.py | Import can create files/load models/rebuild state; I used raw metadata, not the runtime loader |
| Retrieval is filtered and can be biased by workspace context | memory_bridge.py:407 onward; conversation_service.retrieve_memory_context | Workspace bias can change the query vector; the retrieval path can publish a salience event |
| Memory validation is not an absolute “rejected means absent” rule | memory_bridge._validate_before_commit fails open on validator trouble; log_dream_bridge stores flagged entries with validation_warning | This is code behavior, not a claim that a particular harmful entry was admitted |
| RiverBrain learns online quality labels, sandbox labels, and user/peer feedback | echo_model_orchestrator.RiverBrain.learn, learn_from_sandbox_outcome, learn_from_rating, learn_from_council_rating | Counters track heterogeneous events; they are not verified improvements in LLM weights or response quality |
| Brain state is asynchronously persisted | RiverBrain constructor/writer loop/_do_save at echo_model_orchestrator.py:759,1031–1145 | Disk can lag live objects; concurrent producers prevent event attribution from simple differences |
| Self-model is a derived telemetry document | self_model_updater.update at 91–145, _summarize_river, _compute_self_edit_stats | Frequently refreshed does not mean every field has lifetime scope or an independent witness |
| Self-model claim verification relies partly on truthy telemetry fields | self_model_claims.resolve_subject_truth; self_knowledge_verification.find_false_negative_component_claims | Caller-supplied evidence and proposer/verifier names do not themselves prove external independence |
| Provenance primitives distinguish file identity, process facts, and self-report | Actual calls to app/core/provenance_check.py | Their output expressly does not bridge file identity to loaded module execution |
| Self-edit generates, scans, tests, retries, stages, compares fitness, then deploys | self_edit_manager.execute_self_edit and load_self_edit_module | Earlier steps already write/learn; “dry run” only skips later deployment |
| Safety is layered | self_edit_manager F1 scan; sandbox-exec + safe_exec_wrapper; F3 post-write scan/restore; EDIT_FORBIDDEN_TARGETS | Current source supports specific enforcement mechanisms, not a blanket containment guarantee |
| Experimental evidence is separate from execution labels | Existing task-type generator/map/raw/judge files and actual monkeypatch order | Conditions, output metrics, and implemented treatments must be joined independently |

FeralEcho has genuinely useful evidence mechanisms already: trace IDs, raw/truncated council records, retrieval hashes, attempt outcomes, source/process provenance, and liveness check details. The task is to read their scopes correctly before declaring that a mechanism is missing.

## Phase 2 — Representative investigations

### I1 — STATIC SOURCE: what is actually excluded from conversational retrieval?

| Required field | Investigation record |
|---|---|
| QUESTION | Does the current conversation-service filter exclude untagged, autonomous, and recent items, and what does candidates_considered count? |
| EVIDENCE NEEDED | Selection function, its caller/backend, controlled examples covering metadata/age combinations |
| EVIDENCE AVAILABLE | conversation_service.py:88–178; memory_bridge retrieval; an import-free AST extraction of _parse_ts and retrieve_memory_context |
| EVIDENCE UNAVAILABLE | Actual live FAISS ranking and contemporaneous workspace bias were not exercised |
| WHAT I COULD VERIFY | A five-row fixture with untagged-old, autonomous-old, user-old, system-old, user-recent returned only user-old and system-old at k=2 |
| WHAT I COULD ONLY INFER | That a live call with equivalent inputs follows this disk implementation; whether its source tags accurately describe origin |
| WHAT I COULD NOT DETERMINE | Retrieval relevance or truthfulness from filtering correctness |
| CONFIDENCE | High for this narrow deterministic fixture and source semantics; no end-to-end behavioral claim |

Actual fixture output:

```text
- [past interaction]: prior human
- [system log]: system log
```

The provenance counter was **4**, although the search callback returned **5** rows and only **2** were injected. It counts after recency filtering but before final source selection. This is discoverable stage semantics, not missing arithmetic capability. Real backend filtering also excludes code_analysis and self_model_reflection categories before the service layer.

The test executed only the two extracted existing function definitions with a synthetic callback. It did not import conversation_service (whose module loads environment configuration), retrieve real memory, create a test file, or alter application state. It establishes function logic, not the running process's behavior.

### I2 — PROVENANCE: when did the coding template appear, and is the current template still that change?

| Required field | Investigation record |
|---|---|
| QUESTION | Is the current coding synthesis template traceable to a specific committed change despite the dirty working tree? |
| EVIDENCE NEEDED | Parent/commit/current blobs, actual string values, working-tree diff |
| EVIDENCE AVAILABLE | git log/show/diff; AST extraction and SHA256 of template strings |
| EVIDENCE UNAVAILABLE | An immutable version record for every subsequent uncommitted edit or historical process import |
| WHAT I COULD VERIFY | Commit 9ac2f952485a9943c9ce7b1b90f7bea7c873fab9 introduced the coding template; parent lacks it; the general template string is unchanged; both current strings match that commit and HEAD |
| WHAT I COULD ONLY INFER | That the running process uses those bytes, or that the stated commit motivation matches the causal effect claimed |
| WHAT I COULD NOT DETERMINE | Exact timing/author/reason for every dirty change from Git alone; runtime imports are not Git events |
| CONFIDENCE | High for committed/string chronology; limited for executed-version identity |

Commit timestamp: 2026-09-04T23:34:33-07:00. Template SHA256 values:

```text
general: 122b2cf98d2d44e3f68da79cb9b1f1b7dd1ce79e5ee2a80c5d1a7dcaad5bad76
coding:  f71144f2671fee0667ae869072361080256bcaea06ee9ed311e26b5104881553
```

The existing file-identity primitive independently returned current river_deliberation.py SHA256 5d1aa77911509ebbc90d01cd084e5ac3b4c8bd7b9790bc2780b5ce226c253585 versus HEAD blob 836210d27ad655ea7eacc58646882694ef27cda4f5fb0133604e23d88750a9e7, modified_vs_head=true. A file can differ while the specific mechanism under study remains unchanged.

The primitive also correctly reported an untracked experiment script as exists=true/tracked=false/HEAD hash=null, a nonexistent in-root probe path as exists=false, and /etc/passwd as out-of-scope without reading its contents. No probe file was created.

This investigation needed careful source selection, not a new provenance capability.

### I3 — RUNTIME: does the live process use the current source?

| Required field | Investigation record |
|---|---|
| QUESTION | Can I establish that PID 7644 is the intended server, then establish that it has loaded today's provenance/self-edit implementation? |
| EVIDENCE NEEDED | Independent PID/start/cwd/executable observations, application markers, loaded implementation identity |
| EVIDENCE AVAILABLE | Approved ps; existing provenance reader; PID/sentinel files; inspected /health route; source mtimes and loader code |
| EVIDENCE UNAVAILABLE | Loaded module/code-object identities and historical load receipts; no attach/restart permitted |
| WHAT I COULD VERIFY | OS process, expected cwd/interpreter, matching PID markers, progressing heartbeat, responding health endpoint |
| WHAT I COULD ONLY INFER | Application-marker attribution from consistency; current feature availability from source presence |
| WHAT I COULD NOT DETERMINE | Whether current provenance_check.py or self_edit_generated.py bytes are loaded/executed in that process |
| CONFIDENCE | High for external identity and HTTP response; unresolved for loaded-code identity |

Existing reconciliation returned EVIDENCE_AGREES, raw_agreeing_relationship_count=4, independent_corroboration_count=1. It explicitly left observation_time=NEITHER because its input schema contains no observed_at field. This illustrates an existing useful safeguard against counting dependent self-reports as independent witnesses.

PID 7644 began on September 11 UTC. provenance_check.py's observed mtime is September 13T14:25:40Z, and self_edit_generated.py's is September 13T16:11:58Z. These post-start mtimes do **not** prove stale loaded code: lazy import and the explicit self-edit dynamic loader are live alternatives. Conversely, a heartbeat cannot prove reload. Current river_deliberation.py's mtime predates startup, which increases compatibility but still does not identify loaded bytes.

The observation-time omission can be partly handled by recording observer times in this report; it is not evidence that Codex cannot timestamp a command. It does not recover the times of previously unrecorded internal loads or provide an atomic cross-file snapshot.

### I4 — MODEL VISIBILITY: how much of a real model input can be reconstructed?

| Required field | Investigation record |
|---|---|
| QUESTION | Can the latest retained user_conversation turn's exact model-visible input be reconstructed without rerunning it? |
| EVIDENCE NEEDED | User text, history, retrieval, system notes/identity, registry, candidate excerpts, truncation, final transport payload/defaults |
| EVIDENCE AVAILABLE | Four logs joined by trace, source assembly, current metadata and Modelfile |
| EVIDENCE UNAVAILABLE | Full historical system/user request payload, process-local history/registry, per-call model digest and all defaults |
| WHAT I COULD VERIFY | Latest retained user row is the familiar September 14 trace; three candidates and accepted synthesis; one retained retrieval item can be recovered by hash |
| WHAT I COULD ONLY INFER | Delivery of reconstructed context through the successful transport; historical optional-note and identity contents |
| WHAT I COULD NOT DETERMINE | Exact full request bytes or whether all reconstructed content survived budgeting and reached the model |
| CONFIDENCE | High for artifact joins and the recovered item; partial for input reconstruction |

Selection was mechanical: scan interaction_log.jsonl for the latest source=user_conversation record. It again yielded b073d789-b889-4bd3-bc58-ccfd375044e3, already familiar from the earlier review:

- interaction_log.jsonl:20170;
- council_deliberations.jsonl:5006;
- synthesis_integrity_log.jsonl:3486;
- **retrieval_provenance.jsonl:175**.

The retrieval record says candidates_considered=11 and one injected user-conversation item, timestamp 2026-07-21T08:46:01.889980+00:00, text_hash=1a1868362cb1. Searching the current **128,320** metadata records by that hash found exactly one match:

```text
memory ID: cd3bd745-3d9d-47da-813c-e8627333f428
text length: 768 characters
SHA256: 6f95542afb68d3069b547c458e7bf881fc41394217f9c7ff9eb0d164935ad983
```

Metadata file size/mtime were stable across that read. The recovered text is deliberately not duplicated here. A unique short-hash match plus matching metadata strongly supports recovery; a 12-hex hash is not mathematical proof against all possible collisions.

This **narrows an apparent blind spot through existing evidence**. It does not reconstruct the other ten considered items, session history, environmental notes, registry, or final payload. Moreover the provenance log is written after generation from an assembly-side dictionary; it witnesses selection for injection, not independent HTTP receipt.

Source establishes Echo identity prepending, the Qwen English prefix, task-gated synthesis templates, and optional TOOL-LIST. It also shows system-dropping CLI fallback. All three historical was_truncated flags concern candidate excerpts for synthesis, not necessarily generation termination. These distinctions prevent replacing actual model visibility with source intent.

### I5 — STATE / LEARNING: what do the counters mean, and can one attempt be linked to learning?

| Required field | Investigation record |
|---|---|
| QUESTION | Does the self-model's count establish learned competence, and can a retained retry outcome be linked to its exact RiverBrain update? |
| EVIDENCE NEEDED | Metric definitions/windows, attempt records, update inputs and before/after adaptive state, durable event linkage |
| EVIDENCE AVAILABLE | self_model/introspection JSON; reflection shard; 616 retained attempt rows; RiverBrain source; trace joins |
| EVIDENCE UNAVAILABLE | Per-update state receipts and an attributable before/after brain snapshot for the selected attempt |
| WHAT I COULD VERIFY | Windowed attempt-count computation, heterogeneous update semantics, recorded failure→retry success→fitness rejection |
| WHAT I COULD ONLY INFER | That the expected learning call succeeded and was durably saved in that historical execution |
| WHAT I COULD NOT DETERMINE | Exact update multiplicity/state delta attributable to that event, or improved real-world response quality |
| CONFIDENCE | High for metric semantics and recorded outcomes; unresolved for event-level adaptation effect |

At one observation self_model.json reported river_brain.total_observations=194160 and influence_weight=.65. _summarize_river sums introspection.observation_counts. Those counts combine automatically scored responses and feedback updates; learn_from_rating adds three, while sandbox outcomes increment a **separate** sandbox_observation_counts. A large total is not a count of independently verified lessons. Per-task “accuracy” is prediction agreement with training labels, not an independent answer-correctness benchmark.

The self-model also reported total_attempts=28, success_rate=0.0. The retained attempt ledger had **616 distinct trace IDs**, including **seven** terminal successes. This initially looked inconsistent. Source and recalculation resolve it:

- update reads the last **200** reflection-shard entries.
- It counts only entries with generated_code.
- There were **28**: 17 success_dry_run and 11 failed.
- Only result=="success" counts as success, so its reported 0% follows correctly.

This is a metric-scope/labeling hazard, not evidence that the ledger is false or learning disappeared. “Total” here does not mean retained lifetime attempts.

For a concrete adaptive episode, ledger line 470 records trace b3859ce0-8982-4057-9880-f99b70ec6cbe: initial F2 failure, retry F2 success, fitness 3 versus production 4, rejected_not_improvement, deployed=false. Three generation records in each of interaction/council/integrity logs share this attempt trace. The trace is thus useful but not a unique model-call ID.

RiverBrain's sandbox learning method receives model/success/code/error, **no trace_id**. Its successful [SANDBOX] record omits that link. Independently counting retained sandbox_feedback records found **1,302, all without a trace ID**. Failed outcomes have no comparable durable interaction record on that method's failure branch. Timing or code-prefix matching can suggest attribution but cannot prove exactly-once application or persistence amid other producers.

I did not load RiverBrain through its production accessor or unpickle its model state. Those are not justified just to make the table look complete: the constructor starts persistence machinery, and deserialization is not a generic inert JSON read. Aggregate snapshots also would not create the missing event linkage.

The latest retained deployed attempt was 783a4289-f469-4bb2-a889-4ceb708aeec1, started 2026-09-13T16:07:49.966083, accepted at fitness 4 versus production 4. Its record is evidence of the deployment outcome, not proof of the current process's loaded code identity or downstream benefit.

### I6 — SAFETY / AUTHORITY: is a “dry run” a read-only investigative path?

| Required field | Investigation record |
|---|---|
| QUESTION | Can self-edit or retrieval be invoked as a harmless diagnostic under this mission? |
| EVIDENCE NEEDED | Whole call path including imports, preflight, writes, learning, and failure handling |
| EVIDENCE AVAILABLE | self_edit_manager, safe_exec_wrapper, Seatbelt profile, memory_bridge, VectorMemory source |
| EVIDENCE UNAVAILABLE | A new end-to-end run without prohibited writes; not attempted |
| WHAT I COULD VERIFY | dry_run branch occurs after generation, sandbox/testing, and learning; it itself saves reflection/journal; test_code_in_sandbox archives/writes scripts |
| WHAT I COULD ONLY INFER | Which optional paths would fire in a new invocation under current runtime state |
| WHAT I COULD NOT DETERMINE | Current containment efficacy or new candidate behavior through a live test within the one-report-only boundary |
| CONFIDENCE | High that these calls are not read-only; no claimed fresh sandbox validation |

Decisive source locations:

- self_edit_manager.py:1953 saves a reflection before generation.
- test_code_in_sandbox at 1370–1441 creates/archive-copies/writes sandbox scripts before spawning a test.
- execute_self_edit around 2038–2043 and 2071–2097 updates RiverBrain around initial/retry outcomes.
- dry_run at 2138–2157 saves reflection and appends a journal entry before returning a staging path.
- memory_bridge module initialization creates directories/log files and loads embeddings/vector memory.
- VectorMemory._load_or_rebuild_index can persist rebuilt data on a load error.
- retrieve_relevant_memories can publish workspace-consumed salience when query bias is active.

Therefore a search-looking or dry-run-looking API is not automatically a read-only observation primitive. I stopped those portions at source/artifact analysis. This is an authority/side-effect boundary, not inability to execute Python.

The safety architecture itself is more specific than an absolute safety claim: F1 scans code, the test subprocess uses kernel restrictions plus Python-level patches, and F3 scans persisted code before loading/restoring. The Seatbelt file includes explicit /dev write-data allowances as well as scratch writes; its actual rules deserve precedence over simplified “only scratch writes” comments. No claim of a demonstrated escape follows, and no exploit was run.

Protected-target comparisons and proposal paths were read, not exercised. Existing authority limits are not defects simply because they prevent this mission from executing an experiment.

### I7 — SELF-MODEL / EVIDENCE: does “pass” mean a capability is active?

| Required field | Investigation record |
|---|---|
| QUESTION | Can verified_capabilities or a passing liveness ledger substitute for evidence that a specific live mechanism works? |
| EVIDENCE NEEDED | Check definitions, recorded outcomes, witness source, scope of tests versus runtime activity |
| EVIDENCE AVAILABLE | liveness_ledger JSON/source, self_model_claims, self_knowledge_verification |
| EVIDENCE UNAVAILABLE | Independent live activation for every named capability; outside this sampled review |
| WHAT I COULD VERIFY | Ledger had 52 checks, 51 passing at the sampled time; pass fields have materially different meanings |
| WHAT I COULD ONLY INFER | That each recent check ran under the expected current code and reflects relevant live conditions |
| WHAT I COULD NOT DETERMINE | A universal “51 working capabilities” count or blanket independence of self-model evidence |
| CONFIDENCE | High in heterogeneous check semantics; deliberately no overall health score |

Examples at generated_at=2026-09-15T11:14:32.762058+00:00:

- self_edit_apply_to_code passes with status=not_deployed: no hook exists and no false activation claim is made. **Pass does not mean active.**
- self_model_claims_integrity passes four synthetic canary cases. Its source supplies constructed “real_model” and “stale_model” dictionaries; it does not independently observe a running RiverBrain for that test.
- substrate_continuity passes because 1797/1797 sampled logged responses use echo:latest. A model **tag** match is not a model-weights digest or proof of fixed runtime defaults.
- f2_stdin_contract mixes behavioral canaries of a stdin object with source inspection for fd0 closure. It is not a new adversarial kernel-isolation test.

The 19 retained self_model_claims entries include denials marked verified=false. That false refers to the claim's status, not proof RiverBrain is absent. resolve_subject_truth derives truthiness from selected self_model fields; record_claim accepts caller-supplied evidence and checks that proposer/verifier strings differ. Distinct strings are a guard against a simple self-certification mistake, not independent authentication of a witness.

There is enough source to resolve these meanings. Treating all green flags as the same epistemic category would be a reasoning failure, not a missing tool.

### I8 — EXPERIMENTAL EVIDENCE: can the retained task-type experiment identify its treatment?

| Required field | Investigation record |
|---|---|
| QUESTION | Can I verify treatment identity and reuse the saved outcomes without rerunning production? |
| EVIDENCE NEEDED | Actual control flow, condition map, raw responses, scoring records, execution evidence |
| EVIDENCE AVAILABLE | Three experiment scripts; preserved temp artifacts; metadata interception list |
| EVIDENCE UNAVAILABLE | Full experimental candidates/request payloads, executed-script immutable capture, inference seed/digests for every call |
| WHAT I COULD VERIFY | 18 unique IDs in each of raw/map/judge files; no TOOL-LIST; 45 intercepted learns/15 council logs/5 integrity logs; A/B routing defect corroborated |
| WHAT I COULD ONLY INFER | Complete successful transport and absence of all other hidden execution differences |
| WHAT I COULD NOT DETERMINE | Direct-versus-council effect, absent direct treatment; full historical counterfactual |
| CONFIDENCE | High on artifact/control-flow facts; limited causal scope |

This familiar case was rechecked from source and raw files, not the previous report's recommendation. EVIDENCE_DIR is under the OS temporary directory, outside Git, and the analysis script additionally depends on /tmp/real_turn5_response.txt. The artifacts still exist today, so “no raw data” would be wrong. Their preservation across future cleanup is not established.

A/B are identical personal/council inputs because G clears the direct-task set globally and never restores it for A. Better search or a more elaborate tool cannot create the missing direct observations. This is an **experimental-design defect**.

Full model-request reconstruction remains an **artifact-schema limitation**. Existing names, trial IDs, and saved final text do not prove the manipulation reached the model. These are distinct limitations and should not be merged into “insufficient observability.”

## Phase 3 — Empirically identified epistemic failures

The following classifications follow the investigations, not a brainstorm.

| Limitation encountered | Primary classification | Missing capability? | Evidence / narrower interpretation |
|---|---|---|---|
| Default Python cannot import psutil | Environment mismatch | No new primitive indicated | Project interpreter succeeded unchanged |
| ps/curl fail in default tool execution | Security/execution boundary | Not general incapability | Approved reads worked; psutil reader also worked normally |
| Initially looking in app/services or tests/ | Navigation / familiarity | No | rg located app/core/conversation_service.py and actual verification scripts |
| Broad output truncation | Investigation method / output budget | No | Bounded reads and AST extraction recover the relevant code |
| Current file identity unclear | Existing evidence initially not consulted | No | working_tree_file_identity plus Git hashes answered it |
| Specific committed change unclear | Insufficient targeted history inspection | No | Parent/commit/current string comparison resolved it |
| Current bytes versus loaded code | Runtime boundary and absent load evidence in inspected surfaces | Genuine unresolved observation gap, not a proposed tool | Existing process primitive explicitly does not bridge it |
| Missing historical full system/payload | Absent historical data | Genuine evidence gap | Current reconstruction cannot certify past optional/default material |
| Apparently lost retrieved memory | Insufficient join/search | Partly resolved, no new capability needed | Trace → 12-hex hash → unique retained metadata entry |
| Registry name equated with executable exposure | Architectural ambiguity / reasoning error | No | Three different tool mechanisms have separate call paths |
| 28 attempts versus 616 | Metric scope / documentation naming | No | 200-row window reproduced exactly; lifetime/window scopes differ |
| 194160 observations interpreted as 194160 validated lessons | Measurement validity | No tool can justify that inference | Update sources and labels differ; training-count semantics are inspectable |
| Attempt outcome → exact adaptive update/persistence | Missing event linkage, concurrent state | Genuine evidence gap | 1302 sandbox feedback rows lack trace IDs; aggregate means erase provenance |
| Cross-file disagreement at different times | Runtime sampling boundary | Not automatically a defect | Asynchronous self-model/introspection/brain producers; no atomic snapshot |
| “Read”/“dry_run” invocation would write | Side-effect and user-authority boundary | No authority to execute it here | Static traces establish writes; stopped rather than silently running |
| Liveness pass interpreted as active/correct | Measurement/evidence-category error | No | Inert hook can pass; canaries and historical tag ratios answer narrower questions |
| Claim ledger treated as independent verification | Witness-dependence / authority interpretation | No | Telemetry-derived values and caller assertions are not independent instruments |
| Experiment lacks intended direct arm | Experimental-design problem | No missing analysis primitive | No amount of reanalysis can supply absent treatment observations |
| Future artifact location/persistence unclear | Artifact management | Not established as a tool gap | Temp data survived now; durable publication/versioning not guaranteed |
| Historical causal effect or new sandbox outcome | Counterfactual/experimental and authority boundary | Not answerable by read-only inspection | Requires evidence this mission does not generate |

### Which limitations actually constrain reliable understanding?

**Highest-impact unresolved observation gap: identity across execution stages.** I can identify a file, a Git blob, a process, a logged turn, and some injected context. I cannot automatically turn agreement among those facts into proof of the exact code and complete input used in that execution. Evidence fields that name the same repository or trace do not close every transition.

**Second: learning-event attribution.** The system preserves useful attempt outcomes and aggregate adaptive statistics. For the sampled retry, the update path loses the attempt ID and the durable state contains aggregates rather than event receipts. This limits historical attribution even if I can read every current counter. A rising count is not an answer to whether a particular experience improved behavior.

**Third: safe observation versus intervention.** Existing leaf functions show that some useful live inspection is possible without starting FeralEcho or importing its heavy subsystems. Other seemingly diagnostic functions perform writes, model calls, registration, or background work. Reliability depends on identifying that distinction before executing them. No blanket permission to probe production follows from “investigation.”

**Fourth: metric meaning.** Several initially alarming results were resolved completely by inspecting definitions. The remaining risk is semantic inflation: recent-window “total,” synthetic “real_model,” tag-level “continuity,” and a green flag for an honestly absent hook. This is often a reporting/interpretation problem rather than an architectural inability to observe.

### Adversarial checks on this discovery process

- **Am I calling unfamiliarity a blind spot?** No for the interpreter, locations, retrieval hash, or metric window: they were resolved and are classified accordingly.
- **Am I inheriting another agent's design?** No blind-spot report or proposed inventory was opened. Incidental source design comments are disclosed and not adopted as discoveries.
- **Am I relying only on the previous task-type arc?** No: I1, I3's actual capability tests, I5's state calculations/linkage, I6's dry-run boundary, and I7's check semantics add distinct primary investigations.
- **Am I assuming a missing tool where the historical data is gone?** No. Full past payload recovery and absent direct-condition outcomes cannot be manufactured by a tool wrapper.
- **Am I confusing uncertainty with a bug?** No. Stale-looking post-start file mtimes can coexist with lazy/dynamic loading; different self-model/ledger totals have different scopes.
- **Am I declaring the whole architecture deficient from one sample?** No. Findings apply to the inspected paths/artifacts. Other retained evidence might narrow unresolved items.
- **Am I treating self-reports as independent witnesses?** No. The existing reconciliation's single independent corroboration is preserved; liveness/self-model sources are traced.
- **Am I testing beyond authority to reduce uncertainty?** No production model inference, self-edit test, live memory search, registry bootstrap, or brain load was performed.

### Evidence that would change these findings

This is an evidence boundary, **not a tool proposal**. Already-retained records of historical request payloads or code-load identity could narrow I3/I4. Per-update records linking an attempt to exact state changes could narrow I5. A correctly implemented direct-condition dataset would change I8's council-effect limitation. An independently validated metric could justify stronger behavioral claims. Until such evidence is found or separately authorized work produces it, these questions remain bounded as stated.

The narrow conclusion is that Codex's existing investigative abilities are substantial but conditional. The architecture permits reliable answers about many source facts and recorded events. It does not, in the inspected evidence, permit reliable reconstruction of every execution transition or causal learning effect. Preserving those distinctions is more important than inventing an attractive list of capabilities.

## Appendix A — Opening Git status

Full opening `git --no-optional-locks status --short --untracked-files=all` output:

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
?? audits/2026-09-15_codex_task_type_independent_review.md
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

## Appendix B — Evidence fingerprints

Selected SHA256 values, computed read-only during investigation:

```text
5d1aa77911509ebbc90d01cd084e5ac3b4c8bd7b9790bc2780b5ce226c253585  app/core/river_deliberation.py
c863288235dcff3e5f4b56bc956ccb81447ac52c74fa3d2a456d097784715acb  app/core/provenance_check.py
e57b2ef6883e3d5c8cc978d2b7613f643fb271e6be965cc9a5de8e16904e8c1a  app/core/conversation_service.py
5173962947b61aeca6cf6612ef12fa9e16ca869b9c67a57cd3a30d2fd98074ae  app/core/memory_bridge.py
2e747acc5bf353335596ddc75c94025dc51e7866cef6127aa1042fa9a1a0b36a  app/core/self_edit_manager.py
7e64774b5cc7693dafe383918f720024bbbc8e145373d0b8d6685def1f925dc0  app/core/self_model_updater.py
1e32038b532da211890f5a42ded1ed63fa85ed3872fd209fd101226f8a8da2e8  app/core/echo_model_orchestrator.py
7605102d2eb0b9a25c6e5e2704a1efff849a06743334160c4e92a84b170f8cc7  sandbox/safe_exec_wrapper.py
78d1ba29f88b6d9e6d1802899a029db372c82f9a6e6e7ea384686857cbac4ea1  run.py
```

The familiar experiment's primary artifacts remain at /private/var/folders/vg/3mw0sd2j7f12frh367wggw340000gn/T/task_type_behavioral_experiment_20260914_3bd4ed27/:

```text
c931684ade63f318ceb5a15410d81d736d9ecb80704c5a362b5f5ca29a41e1e9  raw_trials_anonymized.jsonl
d688b7c5a292d34d33e3c9d425e71d248e074b61c29add7fc1b13f531f112af7  condition_map_SEPARATE.jsonl
8a9eccd4b606acb35c0e754348765c999549451f6e5ab4147e7c2d2e65753077  judge_scores_anonymized.jsonl
```

Live JSON observations were deliberately not described as simultaneous. For example, an observed self-model last_updated=2026-09-15T11:17:31.991842+00:00 had SHA256 f9fcadec38f2c774ae81e6a7ddfc44bdf31436d653f2db6dd7fb8616c3ed2785; the introspection snapshot read nearby was timestamped 11:16:34.275356+00:00 with SHA256 d0a8114fb3b86af4ac7c0a2df2d230a924dc296c5a5be196179cb309f7450afa. Different generation times are part of the evidence.

## Closing integrity record

Closing repository observation: **2026-09-15T18:21:32Z**. This timestamp does not make the earlier runtime and state observations simultaneous or current at closing.

- Ending Git HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce`, unchanged from opening.
- Ending `git status --short --untracked-files=all`: 168 entries. The full opening status in Appendix A remained present without changed or removed entries; exactly these two entries were added:

```text
?? audits/2026-09-15_codex_michelangelo_blind_spot_discovery.md
?? audits/2026-09-15_task_type_experiment_reconciliation.md
```

The first is this mission's authorized report. The second appeared independently during the observation interval; this mission neither created nor opened it. Its contents and authorship are not inferred.

- Ending path count, using the same `find . -print | wc -l` definition: **22,389**, compared with **22,292** at opening. This live repository was not an isolated filesystem snapshot. The global increase cannot be attributed entirely to this mission, and unchanged Git status lines do not prove unchanged untracked-file contents.
- All nine source-file SHA256 values in Appendix B were independently checked again and remained unchanged.
- The only file directly created or modified by this mission was **this single audit report**. No scratch files, production edits, configuration changes, or deliberate memory/state writes were made. Read-only observations cannot certify that other actors or the running application made no changes. The inspected, approved health GET could produce ordinary server access logging.
- No Git mutation commands were used. No FeralEcho process was intentionally altered: none was stopped, restarted, signaled, or attached to. No model generation, production memory retrieval, brain loading, self-editing, or adaptation was invoked for testing.
- Validation consisted of primary-evidence inspection, the isolated in-memory pure-function fixture, inspected existing provenance functions, read-only process/health observations, artifact checks, and report structure checks. All eight investigations include the requested evidence and uncertainty fields.

The mission ends with an evidence-boundary assessment, not a proposed tool inventory. No prohibited peer blind-spot recommendations were used; the prior exposure and incidental source-comment exposure described above remain explicit limitations on independence.
