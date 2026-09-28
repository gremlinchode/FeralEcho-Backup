# Frozen Experimental Protocol v1.1: Routing Learning vs. Capability Acquisition in a Constructed Learning Pathway

**Protocol version:** v1.1
**Date:** 2026-09-20
**Supersedes (does not modify):** v1.0 — `audits/2026-09-20_persistent_competence_frozen_protocol.md` (sha256 `d1968caf5360e60b8b8d9ca0db9769de4f8bea518ca537a73ea00b8fa5898c06`) and `.json` (sha256 `b35ad16b3c0fed878d74ff404f00892a6be66a8227211510b79e77e50db18131`).
**Motivating review:** `audits/2026-09-20_persistent_competence_protocol_v1_blind_review.md` (verdict: V1.0 REQUIRES REVISION; 12 vulnerabilities V1–V12).
**Companion artifacts:** `audits/2026-09-20_persistent_competence_frozen_protocol_v1_1.json` (machine-readable mirror), `audits/2026-09-20_persistent_competence_v1_to_v1_1_traceability.md` (v1.0 → finding → v1.1 mapping, thought experiments, freeze log).
**Status:** FROZEN when its SHA-256 is recorded in the traceability artifact. No implementation exists. No experimental model has been called. No experimental outcome has been generated or inspected.

---

## §0 Document rules [NORMATIVE]

- **[DOC-1]** Only text inside sections marked `[NORMATIVE]` binds an implementer. Section §24 is `[COMMENTARY]`, has no force, and MUST NOT define any rule (no `**[XXX-n]**` definitions may appear in it). A safeguard that appears only in commentary does not exist.
- **[DOC-2]** This Markdown file governs. The JSON companion is a machine-readable mirror generated from it. If they disagree on any rule, constant, threshold, or arm definition, that is a protocol defect: the freeze is invalid, and any later run showing the disagreement fails conformance (§20).
- **[DOC-3]** Every rule has a unique ID of the form `[PREFIX-n]`, defined exactly once, in its governing section. The JSON `rule_index` maps each ID to its governing section. §22's static checklist verifies both.
- **[DOC-4]** MUST, MUST NOT, and SHALL are binding. Frozen constants are written as `CONST` followed by the constant's name in square brackets, an equals sign, and the value, in the section that governs them; the JSON mirrors them; §22 verifies equality.
- **[DOC-5]** Any element the implementer would otherwise have to choose after this protocol is frozen and that is not specified here or fixed by a P1/P2 commit hash (§21) is a protocol defect, not implementer discretion. The implementer MUST stop and report it (§21), not resolve it silently.

---

## §1 Scope, claims, and definitions [NORMATIVE]

- **[SCOPE-1]** This is a construction experiment. It builds a new, isolated learning pathway (harness, carriers, selector, context builder) and tests it. It reuses only the infrastructure inventoried in §3.
- **[SCOPE-2]** The workers are frozen. Model weights MUST NOT change. Each worker is identified by its Ollama model digest, recorded at P1 and asserted equal at the start and end of every run (§4, [INF-1]). No label in this protocol implies weight learning.
- **[SCOPE-3]** The eligible worker set is exactly E = {`qwen2.5-coder:7b`, `llama3.2:3b`, `deepseek-r1:7b`}. No other worker may be routed to or evaluated. (v1.0's second-generation stage and its fourth worker `gemma3:4b` are removed; see §21 [VER-6].)
- **[SCOPE-4] CLAIM R — ROUTING LEARNING.** Experience improves the selection among the already-capable frozen workers in E. Adjudicated only on Track R (§2, §16).
- **[SCOPE-5] CLAIM C — CAPABILITY ACQUISITION (system-level).** Experience produces a reusable performance improvement of a *fixed* worker (worker identity held constant), through a within-worker mechanism (the context carrier, §7), not explainable by switching to an already-superior pretrained worker. Adjudicated only on Track C (§2, §16).
- **[SCOPE-6]** A routing result MUST NOT be labeled capability acquisition. Capability-acquisition labels are reachable only through Track C. A Track R label and a Track C label are reported separately; neither implies the other.
- **[SCOPE-7] Definitions.** A *task* has a `task_id`, a `capability_id`, a prompt, hidden test inputs and hidden expected outputs. `y(w, t, ctx) ∈ {0,1}` is the oracle outcome (§6) of worker `w`'s completion on task `t` given context `ctx`. A *policy* π maps a task to a worker. A policy's *pass rate* is the mean over tasks of `y(π(t), t, ctx_π)`. "Correct-selection rate" in v1.0 is renamed **pass rate**; there is no other meaning. The *pooled unit* is a (capability, task) pair pooled across the three trained capabilities.
- **[SCOPE-8]** Capabilities: trained = {`list_aggregation` (LA), `string_transformation` (ST), `dict_lookup_merge` (DL)}; adjacent control = `recursion_base_case` (RB); unrelated negative control = `date_arithmetic` (DA). Each capability is defined by a rubric fixed in the generator's docstring and hashed at P1 (§21): LA = traverse a list and combine its elements into a summary value; ST = parse/reformat a string by a stated rule; DL = read/combine/restructure key-value data; RB = correctly handle a base case in a recursive definition over a nested structure; DA = compute a duration, offset, or comparison between calendar dates.
- **[SCOPE-9]** Every reported label MUST carry the suffix "(worker weights unchanged, digest-verified; constructed pathway only)". No report may state or imply that existing FeralEcho components (RiverBrain, `self_model_claims.py`, `behavioral_state.py`, `task_type_classifier.py`, or any production mechanism) possess the tested property.

---

## §2 Hypotheses [NORMATIVE]

Every "p<ALPHA" clause is a one-sided exact paired McNemar test confirmed by the cluster-robust test of [STAT-7], both required to pass, at ALPHA unless stated; every equivalence clause uses the cluster bootstrap of [STAT-2]. "Pooled" means pooled unit over LA, ST, DL. "≥2/3 positive" means the point estimate of the stated gain is >0 in at least two of the three trained capabilities. A hypothesis passes only if every listed clause passes.

Constants: CONST[ROUTE_GAIN_PP]=8, CONST[CTX_GAIN_PP]=10, CONST[CTX_VS_NEUTRAL_PP]=5, CONST[MISMATCH_GAP_PP]=5, CONST[EQUIV_MARGIN_PP]=5, CONST[ALPHA]=0.05, CONST[RETENTION_ALPHA]=0.10, CONST[TREND_MIN_PP]=5, CONST[NEGCTL_MAX_PP]=5, CONST[CONCENTRATION]=0.90, CONST[SECONDARY_WORKER_GAIN_PP]=5, CONST[RETENTION_TOL_PP]=5.

### Track R (routing)

- **[HYP-R0] Informativeness gate G1** (evaluated on DEV only, §10). Track R labels above STATIC-WORKER REDISCOVERY are prohibited unless G1 passes.
- **[HYP-R1] Experience-dependent selection gain.** On pooled E2 (§11): (a) pass(B) − pass(BEST-STATIC-DEV) ≥ ROUTE_GAIN_PP, p<ALPHA; (b) pass(B) − pass(A) ≥ ROUTE_GAIN_PP and pass(B) − pass(A′) ≥ ROUTE_GAIN_PP, each p<ALPHA; (c) pass(B) > pass(SW-w) for every static worker w ∈ E (point estimates, EVAL-measured); (d) ≥2/3 positive versus BEST-STATIC-DEV.
- **[HYP-R2] Ablation.** (a) C is equivalent to A on pooled E2 (bootstrap 90% CI of pass(C) − pass(A) within ±EQUIV_MARGIN_PP); (b) pass(B) − pass(C) ≥ ROUTE_GAIN_PP, p<ALPHA.
- **[HYP-R3] Direction sensitivity (poisoned experience).** pass(A) − pass(E) ≥ ROUTE_GAIN_PP and pass(A′) − pass(E) ≥ ROUTE_GAIN_PP, each p<ALPHA (E worse). **Load-bearing:** failure prohibits every Track R label above CARRIER-CONTROLLED BEHAVIOR ([ADJ-3]).
- **[HYP-R4] Experience specificity.** pass(B) − pass(M) ≥ MISMATCH_GAP_PP, p<ALPHA, where M is the mismatched-experience control (§9).
- **[HYP-R5] Persistence and transport.** All of: (a) B's carrier hash is identical before and after the required restart, in a new process; (b) D (transplant into a fresh instance) has a selection sequence byte-identical to B's; (c) N (null transplant) has a selection sequence byte-identical to A's; (d) each H-BLIND-X arm selects X on every trained-capability task (E2, E3, E5) and its pass rate on them equals SW-X's exactly.
- **[HYP-R6] Routing transfer.** Separately on E3 and on E5 (§11): the [HYP-R1] clauses (a) and (b) hold with ROUTE_GAIN_PP. E6 and E7 are reported but do not enter any Track R label (untrained keys; B ≡ A there by construction; see [EVALM-4]).
- **[HYP-RD] Descriptive (no label effect).** (i) Report pass(B) vs pass(H-DEV) with a bootstrap 90% CI. If the CI lies within ±EQUIV_MARGIN_PP, the report MUST state: "a hand-written carrier built from DEV measurements reproduces the learned effect; this establishes control through the carrier and that the pathway recovers DEV-derivable information from TRAIN experience, not that experience provenance adds causal information." (ii) Report the amputation ladder of §9 [ARM-9].

### Track C (capability acquisition, fixed worker)

- **[HYP-C1] Fixed-worker experience-dependent improvement.** For the primary fixed worker P (§10 [BASE-5]) on pooled E2: (a) pass(P|LEARNED) − pass(P|EMPTY) ≥ CTX_GAIN_PP, p<ALPHA; (b) pass(P|LEARNED) − pass(P|NEUTRAL) ≥ CTX_VS_NEUTRAL_PP, p<ALPHA; (c) for at least one worker W′ ≠ P, pooled E2 pass(W′|LEARNED) − pass(W′|EMPTY) ≥ SECONDARY_WORKER_GAIN_PP (point estimate); (d) ≥2/3 positive for P.
- **[HYP-C2] Context ablation.** Removing the context component from the learned carrier yields prompts hash-identical to EMPTY prompts and outcomes identical to EMPTY (mechanical).
- **[HYP-C3] Direction sensitivity (poisoned context).** pass(P|LEARNED) − pass(P|POISON) ≥ CTX_VS_NEUTRAL_PP, p<ALPHA. **Load-bearing:** failure prohibits every Track C label above CARRIER-CONTROLLED BEHAVIOR ([ADJ-3]).
- **[HYP-C4] Persistence and transport.** (a) The exemplar-store hash is identical before and after the required restart, in a new process; (b) D_C (transplant into a fresh instance) produces prompts hash-identical to LEARNED's and outcomes identical.
- **[HYP-C5] Transfer and negative control.** (a) *Transfer:* on pooled E5, pass(P|LEARNED) − pass(P|EMPTY) ≥ CTX_GAIN_PP, p<ALPHA, **and** pass(P|LEARNED) − pass(P|NEUTRAL) ≥ CTX_VS_NEUTRAL_PP, p<ALPHA (so a format-compliance effect shared with format-matched neutral context cannot earn transfer). (b) *Negative control:* on E7 (unrelated capability, DA) the gain pass(P|LEARNED) − pass(P|EMPTY) ≤ NEGCTL_MAX_PP **or** p ≥ ALPHA (not significantly positive), **and** the negative control is informative: pass(P|EMPTY) on E7 lies within [NEGCTL_BAND_LOW, NEGCTL_BAND_HIGH] (a floor- or ceiling-saturated control cannot show a confound and therefore fails this clause). A significant E7 gain, or an uninformative E7, blocks every Track C label above CARRIER-CONTROLLED BEHAVIOR. E6 (adjacent) is reported, not label-determining. Constants: CONST[NEGCTL_BAND_LOW]=0.20, CONST[NEGCTL_BAND_HIGH]=0.90.
- **[HYP-C6] Accumulation.** §12. Requires new gain on fresh sealed tasks, retention, restart survival, freshness, and no carrier-arithmetic evidence.

---

## §3 Infrastructure inventory and sandbox interface [NORMATIVE]

- **[INFRA-1] EXISTING INFRASTRUCTURE USED UNMODIFIED:** (i) the macOS `/usr/bin/sandbox-exec` binary and its Seatbelt kernel enforcement; (ii) the Python interpreter of the `feral_echo` conda environment (absolute path and version recorded at P1); (iii) a byte-for-byte copy of `app/experiments/raoc/approach_classifier.py`, pinned by source hash at P1, used only to bucket reference solutions ({RECURSIVE, ITERATIVE, NO_EXPLICIT_CONTROL_FLOW, UNKNOWN}). Nothing else in FeralEcho is used.
- **[INFRA-2] EXISTING INFRASTRUCTURE EXPLICITLY NOT USED:** `sandbox/run_script.py::run_sandbox_script_isolated()` (no `env` or profile parameter; inherits the parent environment; `cwd=os.getcwd()`), `sandbox/echo_sandbox.sb` (grants global `(allow file-read*)`), and `sandbox/safe_exec_wrapper.py` as-is (inserts the repository root into `sys.path`). The harness MUST NOT import or invoke them. v1.0's description of these as "reused unmodified" is withdrawn.
- **[INFRA-3] NEW EXPERIMENTAL HARNESS / SECURITY LAYER REQUIRED** (all hashed at P1): `oracle_runner.py` (spawns the solver process), `frozen_protocol_oracle.sb` (Seatbelt profile), `solver_wrapper.py` (in-sandbox driver; may copy `safe_exec_wrapper.py`'s Python-layer patch functions but MUST omit any insertion of the repository root or any project path into `sys.path`; a diff against the source is recorded as evidence).
- **[INFRA-4] Frozen sandbox interface.**
  - *Profile:* default-deny. `(deny network*)` including loopback (the solver cannot reach Ollama). `process-fork` denied. `process-exec` allowed only for the recorded interpreter path.
  - *Filesystem reads:* an explicit allow-list `READ_ALLOW`, generated at P1 by tracing a known-good solver run, stored as a hashed file, and containing only the interpreter prefix, standard-library and site-packages trees, system libraries the trace shows are required, the per-episode scratch directory, and `/dev`. It MUST NOT contain the repository root, `HIDDEN_ROOT`, `PROMPT_ROOT`, `SCRATCH_ROOT`'s parent, or any ancestor of `HIDDEN_ROOT`. Explicit denies for `HIDDEN_ROOT`, `PROMPT_ROOT`, the repository root, and the user home directory (other than the interpreter prefix and scratch) MUST be present, and their effectiveness MUST be shown by §14 exploits, not assumed from rule ordering.
  - *Filesystem writes:* only inside the per-episode scratch directory.
  - *Environment allowlist:* exactly `PATH=/usr/bin:/bin`, `PYTHONHASHSEED=<seed>`, `MPLBACKEND=Agg`, `HOME=<scratch>`, `TMPDIR=<scratch>`, `LANG=C.UTF-8`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`, passed through `subprocess`'s `env=` argument. `os.environ.copy()` and omission of `env=` are forbidden.
  - *Prompt location:* `PROMPT_ROOT`, outside the repository, read only by the orchestrator, never mounted for the solver. Model prompts are built in orchestrator memory.
  - *Hidden evaluator location:* `HIDDEN_ROOT`, outside the repository, mode 0700, holding expected outputs, reference solutions, and grading code. Read only by the orchestrator and never by the solver process.
  - *Temporary directories:* one fresh scratch directory per solver invocation under `SCRATCH_ROOT`, resolved with `realpath`, deleted after grading.
  - *Flow:* the orchestrator writes `candidate.py` and `inputs.json` (test **inputs** only) into scratch; the sandboxed `solver_wrapper.py` calls `solve` on each input and writes `outputs.json`; the orchestrator, outside the sandbox, compares `outputs.json` to the hidden expected outputs. Expected outputs and reference solutions never enter any solver process.
- **[INFRA-5]** If secure isolation cannot be implemented to the point that every §14 exploit in [QUAL-2] fails as required, the adjudication is APPARATUS INVALID and no learning episode may run.
- **[INFRA-6]** Forbidden imports in the harness: any module of `app.*` (including `app.core.echo_model_orchestrator`, `river_deliberation`, `task_type_classifier`, `self_model_claims`, `behavioral_state`, `memory_bridge`, `ollama_handler`), `run.py`, and `sandbox.*`. The harness calls Ollama's HTTP API directly with its own client. No FeralEcho production identity injection is applied.

---

## §4 Inference conditions [NORMATIVE]

The following are frozen. No value may be changed after P1 (§21).

- **[INF-1] Model identity.** Workers by Ollama tag and digest. The harness MUST read each digest from `GET /api/tags` at run start and run end and assert equality with the P1-recorded digest. The Ollama server version is recorded.
- **[INF-2] Endpoint and shape.** `POST /api/chat`, `stream=false`, messages = [system, user], no tools, no `format` constraint, `think` left at the server default. Each request is a fresh single-turn conversation: no history, no carried-over Ollama `context`, no retrieval other than the frozen context block of §7.
- **[INF-3] Sampling.** CONST[TEMPERATURE]=0, CONST[TOP_P]=1.0, CONST[TOP_K]=1, CONST[OLLAMA_SEED]=20260920. Limits: CONST[NUM_PREDICT]=2048 tokens, CONST[NUM_CTX]=8192. If the runtime does not guarantee bitwise determinism at these settings, that is expected: the realized completion is recorded once in the ledger (§6 [ORC-4]) and is the evidence; generation determinism is not assumed.
- **[INF-4] System prompt** (exact bytes): `You are a careful Python programmer. Respond with exactly one fenced Python code block that defines the function `solve` as specified. Do not include explanations, tests, or example calls outside the code block.`
- **[INF-5] User prompt template** (exact structure): `Task:\n{task_description}\n\nFunction signature:\n{signature}\n\nExamples (illustrative only):\n{illustrative_examples}\n{context_block}\nWrite the function `solve` now.` where `{illustrative_examples}` is the first two entries, by index, of that capability's five fixed illustrative examples (never graded), and `{context_block}` is the empty string for EMPTY context, else `\nWorked solutions to related tasks (for reference):\n` followed, for each exemplar in stored order, by `\n### Example {i}\nTask:\n{exemplar_task}\nSolution:\n```python\n{exemplar_code}\n```\n`. An EMPTY-context prompt is therefore byte-identical to the base prompt.
- **[INF-6] Code extraction.** Remove any `<think>...</think>` span. Take the last closed fenced Python code block in `message.content`. If none, accept `message.content` only if the whole remainder parses as Python. Otherwise the output is *malformed*. Only `message.content` is read; `thinking` fields are ignored.
- **[INF-7] Output-handling outcomes, all scored `y=0` and counted (never excluded, never retried):** malformed output; refusal or any response containing no code; empty output; generation timeout; truncation (`done_reason="length"`) that leaves no closed code block. Each is recorded with its category.
- **[INF-8] Timeouts.** CONST[GEN_TIMEOUT_S]=180 per generation request (timeout ⇒ `y=0`, no retry). CONST[EXEC_TIMEOUT_S]=10 per solver-wrapper run.
- **[INF-9] Retry and crash policy.** Retries are permitted only for *infrastructure faults* (Ollama unreachable, HTTP 5xx, sandbox launch failure not attributable to candidate code), at most CONST[RETRY_MAX]=3 with fixed backoff. A fault still unresolved after RETRY_MAX halts the run; it is never converted into an exclusion or a failure. Resumption is idempotent through the ledger.
- **[INF-10] Duplicate outputs.** Identical outputs are permitted and are not deduplicated; each output's hash is recorded and cross-task duplicate counts are reported.
- **[INF-11] Concurrency and scheduling.** Requests are issued sequentially (concurrency 1). The (worker, task) generation order is a seeded shuffle (CONST[GEN_ORDER_SEED]=5042026) recorded before generation. `keep_alive` is the constant `"10m"`.
- **[INF-12] Prompt size.** Every prompt's token count MUST be ≤ NUM_CTX − NUM_PREDICT; a violation aborts the run. Context blocks are never truncated.
- **[INF-13] Parameters the runtime cannot control** (bitwise generation determinism, internal think-token budgeting) are recorded per request (`done_reason`, `eval_count`, request-body hash, response hash) and handled only by [ORC-4] and [EXC-3]. They MUST NOT be worked around after P1.
- **[INF-14]** The inference-settings hash (over [INF-1]–[INF-13] as realized) is recorded for every request and MUST be identical across every request in a comparison; a mismatch invalidates that comparison ([CONF-3]).

---

## §5 Partitions, pilot, and sealing [NORMATIVE]

Frozen constants: CONST[N_PILOT]=20, CONST[N_DEV]=60, CONST[N_TRAIN]=60, CONST[N_QUAL]=20, CONST[N_EVAL_E2]=150, CONST[N_EVAL_E3]=75, CONST[N_EVAL_E5]=75, CONST[N_EVAL_E6]=75, CONST[N_EVAL_E7]=75, CONST[N_LONG_TRAIN_ROUND]=20, CONST[N_LONG_EVAL_BLOCK]=60, CONST[N_DA_REF]=12, CONST[MASTER_SEED]=20260920.

| Partition | Capabilities | Size (per capability) | Purpose (frozen) | Exposure |
|---|---|---|---|---|
| PILOT | LA, ST, DL, RB, DA | N_PILOT | Harness debugging, generator validity, determinism probe, timeout feasibility. **Never** used to tune prompts, extraction, sampling, thresholds, or worker choice. | Free |
| DEV | LA, ST, DL (N_DEV each); DA (N_DA_REF) | as stated | Static-worker baselines; best-static selection; gate G1; primary-worker rule; H-DEV and handwritten-context construction; DA reference exemplars. Measured **once** under frozen conditions. | Measured once, after P1 |
| TRAIN | LA, ST, DL | N_TRAIN | The only source of learning experience for B, E, M, C-track LEARNED/POISON. | After P1 |
| LONG_TRAIN | LA only | 4 × N_LONG_TRAIN_ROUND | Longitudinal experience blocks (§12). | After P1 |
| QUAL | LA, ST, DL | N_QUAL | Oracle qualification (§14 [QUAL-3]). | After P1 |
| EVAL cell E2 (same-context, new task) | LA, ST, DL | N_EVAL_E2 | Primary held-out tests. **Sealed.** | Stage 3 only |
| EVAL cell E3 (surface-changed) | LA, ST, DL | N_EVAL_E3 | Routing transfer. Sealed. | Stage 3 only |
| EVAL cell E5 (structurally novel) | LA, ST, DL | N_EVAL_E5 | Transfer. Sealed. | Stage 3 only |
| EVAL cell E6 (adjacent capability) | RB | N_EVAL_E6 | Reported, not label-determining. Sealed. | Stage 3 only |
| NEGCTL = EVAL cell E7 (unrelated capability) | DA | N_EVAL_E7 | Negative control (§2 [HYP-C5]). Sealed. | Stage 3 only |
| LONG_EVAL | LA only | 4 × N_LONG_EVAL_BLOCK (each block 30 same-family + 30 structurally novel) | Fresh sealed accumulation tests. Sealed, one block per round. | Stage 3 only, block *j* only at round *j* |
| E1 (replay/memorization) | LA, ST, DL | 20 TRAIN tasks re-presented | Memorization reference for Track C only; excluded from every label. | Stage 3 |

- **[PART-1]** Partitions are pairwise disjoint by `task_id`, by normalized prompt hash, and by generator template instance. The harness MUST assert this at startup and at each stage boundary.
- **[PART-2] Structural novelty (E5, LONG_EVAL novel half).** Cell membership is fixed by generator metadata, computed before any worker sees any task: an E5 task's `template_family_id` differs from every TRAIN/LONG_TRAIN family for that capability, **and** its reference solution's approach bucket ([INFRA-1]) differs from every bucket used by that capability's TRAIN/LONG_TRAIN reference solutions. The generator's family table MUST make this possible and the P1 commit MUST record it. Each capability's E2 and E3 cells MUST span at least CONST[MIN_FAMILIES_E2]=10 and CONST[MIN_FAMILIES_E3]=10 distinct template families, and its E5 cell at least CONST[MIN_FAMILIES_E5]=5 distinct novel families, so that cluster-level inference ([STAT-7]) is possible; a generator that cannot meet these minimums is defective (APPARATUS INVALID). E3 keeps the same family and bucket as some TRAIN family with renamed identifiers and reworded prompt.
- **[PART-3] Pilot rules.** PILOT may be run any number of times but only on the PILOT partition. Any change to the generator, harness, or thresholds that a PILOT run motivates MUST be recorded in the `pilot_decision_log` (what, why, timestamp) and MUST be complete before P1. PILOT MUST NOT be used to tune prompt text, extraction, sampling parameters, timeouts, or retry policy: those are fixed by §4. If PILOT shows §4's conditions to be unusable (e.g. an extraction-failure rate above 50% for a worker on PILOT), that is a protocol defect: the response is a new protocol version, created before any DEV or EVAL exposure ([VER-2]), not a tuning of §4.
- **[PART-4] Sealing (commit–reveal).** P1 is a Git commit containing the generator, templates, reference solutions' generator code, harness, sandbox layer, analysis and adjudication code, `READ_ALLOW`, the digests of §4 [INF-1], the constants of this protocol, and the `pilot_decision_log`. DEV, TRAIN, LONG_TRAIN, QUAL and PILOT seeds derive from MASTER_SEED. **The EVAL and LONG_EVAL seed is `SHA-256("EVAL" ‖ P2_commit_hash)`**, where P2 is a later commit (§21 [VER-1]) that records the DEV-derived decisions of §10. EVAL is therefore unknowable before P2 and depends on every frozen artifact; any change to the generator changes EVAL.
- **[PART-5] EVAL confinement.** EVAL and LONG_EVAL instances MUST NOT be materialized (in memory, on disk, or in any log) before Stage 3 begins; the harness MUST assert their absence at Stage 3 start and record the first-materialization timestamp in an `eval_exposure_log`. No task, template instance, answer, evaluator artifact, or model output from sealed EVAL may be used to tune prompts, select a worker, choose a handwritten carrier, alter a threshold, modify extraction, change a timeout, modify a retry policy, or debug behavior. Interim analyses of EVAL results are forbidden; analysis may begin only when every ledger for Stage 3 is sealed.
- **[PART-6] Exposure invalidation.** If any of the uses forbidden by [PART-5] occurs, or EVAL is exposed before Stage 3, protocol v1.1 fails for that run: the run's adjudication is APPARATUS INVALID and a new protocol version with a new P2 is required before any further run.
- **[PART-7]** Task-validity replacement is allowed only before any worker output exists for that task: the automated check that a task's reference solution passes its own tests (and fails a frozen set of mutations) runs at generation; a failing candidate task is replaced by the generator's next candidate in its deterministic stream. This check depends on no worker output. Replacements exceeding CONST[MAX_REPLACEMENT_RATE]=0.05 of candidates in any partition mean the generator is defective (APPARATUS INVALID).

---

## §6 Oracle, grader identity, exclusions, and nondeterminism [NORMATIVE]

- **[ORC-1] Oracle.** Grading executes candidate code in the §3 sandbox on the hidden test inputs (two runs, under CONST[HASHSEED_1]=1042026 and CONST[HASHSEED_2]=2042026), then compares outputs to the hidden expected outputs in the orchestrator. `y=1` iff both runs terminate normally, both output sets are identical to each other, and all outputs equal the expected outputs. Anything else is `y=0`. The oracle returns only `{0,1}`; there is no partial credit, free-text feedback, or confidence.
- **[ORC-2] Nondeterministic-task handling.** Disagreement between the two hash-seed runs is scored `y=0` (category `nondeterministic`), counted, and never excluded. It enters carrier updates as `x=0.0`.
- **[ORC-3] Grader identity.** Pre-registered at P1 and recorded in the `grader_manifest`: SHA-256 of the grading function's source, of the `oracle_runner.py`/`solver_wrapper.py`/profile source, of every hidden test-artifact file (per-task expected-output file and reference solution), and of the task manifest. Before every run and every arm, the harness recomputes these hashes and compares them to the manifest. **Any mismatch invalidates every comparison involving that run** ([CONF-3]); a load-bearing mismatch yields APPARATUS INVALID. One grading function is used for all arms; a per-arm variant is forbidden.
- **[ORC-4] Completion ledger and freshness.** The `CompletionService` returns a completion for a key `(namespace, worker_id, prompt_hash)`. Within a namespace, a key is generated once and stored append-only (request body, response, `done_reason`, `eval_count`, oracle outcome, hashes); later requests for the same key read the stored value. Namespaces: `NS_TRAIN`, `NS_DEV`, `NS_MAIN` (all Stage 3 arms), `NS_REPL` (arm A′ only), `NS_LONG_j` (round *j*), `NS_LONG_RET` (retention regeneration). **Reads across namespaces are forbidden**; a runtime counter `cross_namespace_hits` MUST equal 0, and a static check confirms no code path can read another namespace. Cached prior outputs are therefore never reusable as new evidence.
- **[EXC-1] Allowed exclusion reasons.** Exactly one: task-validity replacement before any worker output exists ([PART-7]). No episode may be excluded for any reason that depends on a worker output, an outcome, or an arm.
- **[EXC-2] Forbidden.** Post-hoc exclusion; excluding tasks because they are hard, nondeterministic, timed out, malformed, or inconvenient; excluding a task from one arm and not another; reclassifying a failure as an infrastructure fault.
- **[EXC-3] Denominators and replacement.** The denominator of every pass rate is the full frozen task manifest for that cell. Malformed, timed-out, truncated, empty, refused, and nondeterministic episodes are in the denominator as `y=0`. No task is replaced after any worker output exists for it. An unresolved infrastructure fault halts the run ([INF-9]).
- **[EXC-4] Maximum exclusion rate.** Post-exposure exclusions: zero permitted. Pre-exposure replacements: at most MAX_REPLACEMENT_RATE (§5 [PART-7]). Exceeding the cap ⇒ APPARATUS INVALID. The exclusion count and every replacement (with reason) are logged and reported per partition.

---

## §7 Carrier and learning pathway [NORMATIVE]

A *carrier* has two components. Consumers read only the fields named below; provenance and timestamp fields are stored for audit and MUST NOT be read by `score()` or by the context builder (verified statically, §22).

- **[CAR-1] Routing component.** One JSON file per (worker_id, capability_id): `{worker_id, capability_id, count:int≥0, mean:float∈[0,1], last_updated_utc:str|null, provenance:str}`. Cold start: `count=0, mean=0.5, last_updated_utc=null, provenance="cold"`, code-identical in every arm.
- **[CAR-2] Routing update rule.** On an oracle-graded episode with `x∈{0.0,1.0}`: `count += 1; mean += (x − mean)/count`. This is an exact, uncapped cumulative mean (order-invariant). It is deliberately not RiverBrain's capped `_MEAN_EFFECTIVE_WINDOW` formula.
- **[CAR-3] Consumer.** `score(worker_id, capability_id)` opens the one file (no in-process caching); returns 0.5 if `count < CONST[MIN_OBS]=5`, else `mean`. Pure; no write access.
- **[CAR-4] Context component.** Per (worker_id, capability_id), a JSON list of at most CONST[K_MAX]=8 exemplars `{exemplar_id, exemplar_task, exemplar_code, source_task_id, provenance}`. The context builder reads only `exemplar_task` and `exemplar_code`, in stored order, into `{context_block}` ([INF-5]).
- **[CAR-5] Context update rule.** For the primary carrier (arms B-type in Track C), the store for (w, c) is the first CONST[K_CONTEXT]=4 oracle-passing episodes of worker w on TRAIN capability c, in the seeded TRAIN order (CONST[TRAIN_SHUFFLE_SEED]=3042026). Fewer than K_CONTEXT passes ⇒ the store holds what exists (logged). The rule reads no EVAL or DEV information. Longitudinal stores follow §12.
- **[CAR-6] Serialization.** Atomic write-to-temp then `os.replace`; no `pickle`, no `fcntl`, no background thread, no module-level singleton or cache, no `get_X()` shared-instance accessor. Every read is a fresh `open()`/`json.load()`.
- **[CAR-7] Allowed mutation points and write audit.** Exactly two functions may write a carrier file. `_record_episode()` (routing update; context update per [CAR-5]/§12) is called only by `learn()`, and is the sole writer for arms B, E, M, LEARNED, and LB (E and M feed it inverted or relabeled real episodes). `_write_carrier()` is the sole writer for arms defined by construction: C, D, N, H-BLIND-X, H-DEV, the amputation ladder, NEUTRAL, HANDWRITTEN, POISON, D_C, and LN's neutral exemplars. A third write path means the protocol is impossible as specified ([DOC-5]). **Every carrier write MUST be logged** with `(arm_id, writing_function, call_site, hash_before, hash_after)`; conformance ([CONF-1]) MUST show that every write into the root of B, E, M, LEARNED, or LB came from `_record_episode()` and that no hand-constructed value entered any such root. A hand-written carrier presented as a learned arm is a load-bearing conformance FAIL.
- **[CAR-8] State identity and hashing.** Each arm has its own filesystem root (`runs/<arm_id>/`), separate process, and state hash (SHA-256 over the sorted carrier file list and contents), logged at four checkpoints: after initialization, after construction/learning, after any restart/transplant/ablation operation, after evaluation.
- **[CAR-9] Learning pathway.** `learn(worker_id, capability_id, task)`: obtain the completion from the `CompletionService` (`NS_TRAIN`), grade it with the oracle, append `{episode_id, worker_id, capability_id, task_id, timestamp_utc, oracle_outcome, output_hash, arm_id}` to the experience ledger (never storing answer content), then call `_record_episode()`. The experience ledger is never read by `score()` or the context builder. Every worker in E receives exactly all N_TRAIN tasks per trained capability (forced exploration; no selector-driven allocation), in the seeded order. **No arm may contain a partially-trained routing state** except H-BLIND-X by design ([ARM-6]).
- **[CAR-10] Matched experience.** B, E, M, and the Track C LEARNED/POISON/NEUTRAL constructions all derive from the same `NS_TRAIN` ledger, so they differ only in how the carrier is constructed from identical experience.

---

## §8 Selector and tie policy [NORMATIVE]

- **[SEL-1] Routing selection.** For a task in capability c, the selector chooses `argmax_{w∈E} score(w, c)`. Selection is deterministic given carrier state, task, and tie key. In Mode R the prompt contains no context block ([EVALM-1]).
- **[TIE-1] Tie policy.** Alphabetical or any identity-ordered tie-breaking is forbidden. Let T be the tied worker set. Sort T by `SHA-256(worker_id)` (a fixed canonical order, not an ordering by name). The chosen index is `int.from_bytes(HMAC-SHA256(key=TIE_KEY, msg=f"{task_id}|{capability_id}|{'|'.join(sorted_T)}")[:8], "big") mod |T|`.
- **[TIE-2] Keys and matching.** CONST[TIE_KEY_MAIN]=pc-v1.1-tie-main is used by every arm except A′. CONST[TIE_KEY_REPL]=pc-v1.1-tie-repl is used by A′ only. Because the draw depends only on (task, capability, tied set, key), arms with identical scores make identical selections (matched across arms by construction), and A′ is an independent random policy.
- **[TIE-3] Independence, recording, replay.** The tie draw uses no worker outcome, no arm state, and no clock. Every selection records `(task_id, capability_id, tied_set, tie_key_id, tie_index, chosen_worker)`; the entire selection sequence of any arm can be replayed offline from carrier state and task ids and MUST match the recorded sequence (checked in §20).
- **[TIE-4] No identity bias.** The policy MUST NOT systematically favor any named worker. This is demonstrated, not assumed, by [QUAL-4].

---

## §9 Arms and controls [NORMATIVE]

All arms run in separate OS processes with separate roots ([CAR-8], [ISO-*]). Track R arms are evaluated in Mode R; Track C arms in Mode C (§11).

**Track R arms (routing carrier; all Mode R):**

- **[ARM-1] A — cold baseline.** Cold carrier, TIE_KEY_MAIN, completions from `NS_MAIN`. Under a cold carrier the selector is uniform random over E per task.
- **[ARM-2] A′ — independent replicate.** Cold carrier, TIE_KEY_REPL, completions regenerated into `NS_REPL` (independent generation). Estimates run-to-run noise of the random-policy pipeline.
- **[ARM-3] B — learned.** All cells of E×{LA,ST,DL} trained by `learn()` ([CAR-9]); a required kill-and-restart occurs after learning and before evaluation; hashes logged.
- **[ARM-4] C — ablation.** Begins from B's post-restart files copied byte-for-byte into `runs/C/`; every routing cell is reset to cold via `_write_carrier()`.
- **[ARM-5] D — experience-derived transplant.** A fresh instance (new process, new root, no history) receives B's post-restart routing carrier files, key-for-key (no re-keying), via `_write_carrier()`. D reads no experience ledger.
- **[ARM-6] H-BLIND-X, X ∈ E — handwritten, information-free.** A fresh instance; the only writes are `_write_carrier()` setting, for every trained capability, worker X's cell to `count=60, mean=0.9`, all other cells cold. The value is a fixed constant chosen with no measurement access; it encodes the static policy "always X" through the carrier. Three arms, one per X, fixed before any data exists.
- **[ARM-7] H-DEV — handwritten, DEV-informed.** A fresh instance; for every (w, c) trained cell: `count=60, mean=` the DEV pass rate `r_{w,c}` from §10. Chosen by this rule alone, from DEV data only; no EVAL information may influence it ([PART-5]).
- **[ARM-8] N — null (cold) transplant.** A fresh instance undergoing the identical transplant procedure of D, but the written content is the cold values for every cell.
- **[ARM-9] Amputation ladder (descriptive).** Applied to D's carrier: L1 quantize `mean` to one decimal; L2 quantize to three buckets {0.25, 0.5, 0.75}; L3 replace `count` with the fixed value 60; L4 delete `last_updated_utc` and `provenance` (MUST yield byte-identical selections). Report the coarsest level whose selection sequence and pass rate are within EQUIV_MARGIN_PP of D. Not label-determining. (v1.0's structurally-null L5–L8 are removed.)
- **[ARM-10] E — poisoned experience.** Fresh cold instance; the same `NS_TRAIN` episodes as B, but every oracle outcome is inverted (`x→1−x`) at the call site before `_record_episode()`; the oracle is never told to lie. Same restart requirement as B.
- **[ARM-11] M — mismatched experience.** Fresh cold instance; the same `NS_TRAIN` episodes, but each capability's cells are fed the episodes of a different trained capability by the fixed cyclic map LA←ST, ST←DL, DL←LA (real oracle outcomes, wrong capability label). Same restart requirement as B.
- **[ARM-12] Static-worker baselines (computed, no carrier).** SW-w for each w ∈ E: pass rate of always choosing w, from `NS_MAIN`. RAND: expected pass rate of uniform-random worker choice, computed exactly from `NS_MAIN`. BEST-STATIC-DEV: the worker `S_global` of §10 [BASE-2]. BEST-STATIC-PERCAP-DEV: per-capability DEV-best workers, reference only. All are evaluated on the same E cells as the learned arms.
- **[ARM-13] Fixed-worker invariance control (Track R).** For each w ∈ E, evaluation with worker w fixed under B's routing carrier and under the cold carrier MUST generate byte-identical prompts (hash-equal) and hence identical outcomes; otherwise the routing carrier leaks into worker-level input and the apparatus is invalid ([QUAL-5]).

**Track C arms (context carrier; all Mode C, worker fixed). Base = EMPTY context.**

- **[ARM-14] EMPTY.** `context_block=""`; identical to the static-worker base prompt; shares `NS_MAIN` completions with SW-w.
- **[ARM-15] LEARNED.** Per (w, c), the store built by [CAR-5] from `NS_TRAIN`. Run for every w ∈ E.
- **[ARM-16] NEUTRAL.** Format-matched: K_CONTEXT exemplars taken in order from the DA reference-solution pool (N_DA_REF) — a different capability, same template. Run for P only.
- **[ARM-17] HANDWRITTEN (H_C).** K_CONTEXT exemplars per capability taken in order from that capability's DEV reference solutions (authored by the generator, never by any worker, no EVAL access). Run for P only.
- **[ARM-18] POISON.** LEARNED's store with each exemplar's code replaced by the first mutation, from a frozen ordered mutation-operator list (hashed at P1), that makes it fail its own source task's hidden tests (verified with the oracle on TRAIN; an exemplar with no failing mutation is dropped and the shortfall logged). Format identical to LEARNED. Run for P only.
- **[ARM-19] D_C.** A fresh instance receiving LEARNED's post-restart context store (P only), verifying hash equality.
- **[ARM-20]** Required restart for LEARNED after construction and before evaluation; hashes logged.

---

## §10 Baselines and DEV calibration [NORMATIVE]

Frozen constants: CONST[HEADROOM_PP]=8, CONST[BEST_MARGIN_PP]=5, CONST[P_RANGE_LOW]=0.30, CONST[P_RANGE_HIGH]=0.85.

- **[BASE-1] DEV measurement.** Under §4's frozen conditions, each w ∈ E attempts every DEV task for LA, ST, DL (once, into `NS_DEV`). DEV pass rates `r_{w,c}` (N_DEV each) and their pooled means are recorded. This is the only use of DEV; DEV is never re-measured. DEV MUST NOT be used to tune anything in §4.
- **[BASE-2] Best-static selection without EVAL.** `S_global = argmax_w mean_c r_{w,c}` (pooled over LA, ST, DL). Ties are broken by `SHA-256(worker_id)` order. `S_percap(c) = argmax_w r_{w,c}` (reference only). Neither uses EVAL.
- **[BASE-3] Gate G1 (routing informativeness).** G1 passes iff all of: (a) the headroom `mean_c r_{S_percap(c),c} − mean_c r_{S_global,c} ≥ HEADROOM_PP`; (b) `S_percap(c)` takes at least two distinct values across LA, ST, DL; (c) in at least two capabilities the best worker exceeds the second-best by ≥ BEST_MARGIN_PP; (d) *heterogeneity is not a format artifact*: the headroom of (a), recomputed on only those DEV tasks for which all three workers produced a well-formed, complete output (no [INF-7] category for any worker on that task), is ≥ CONST[HEADROOM_CLEAN_PP]=5. If G1 fails, Track R adjudicates to STATIC-WORKER REDISCOVERY ([ADJ-1]); Track C is unaffected.
- **[BASE-4] Reporting.** DEV and (after Stage 3) EVAL pass rates of every worker on every cell, including RB and DA, and per-worker rates of malformed, truncated, timed-out, and nondeterministic outcomes, MUST be reported so that a global worker advantage cannot be mistaken for learning. The EVAL routing gain MUST additionally be decomposed into the part attributable to avoiding [INF-7] failures and the part attributable to correctness differences among well-formed outputs; any Track R label MUST state both parts. Track R results hold under the frozen inference conditions of §4, including their effect on each worker's output format.
- **[BASE-5] Primary fixed worker P (Track C).** Among workers whose pooled DEV pass rate lies in [P_RANGE_LOW, P_RANGE_HIGH], P is the one with the lowest pooled DEV pass rate; if none lies in range, P is the worker whose pooled DEV pass rate is closest to 0.5. Ties by `SHA-256(worker_id)` order.
- **[BASE-6] H-DEV construction.** [ARM-7] uses only these `r_{w,c}`.
- **[BASE-7]** The DEV-derived decisions (`S_global`, `S_percap`, G1 outcome, P, H-DEV values, HANDWRITTEN and NEUTRAL exemplar selections) and the sealed DEV ledger's hash-chain head are recorded in the P2 commit before any EVAL materialization. A second DEV measurement is forbidden; a DEV ledger whose chain head differs from the one in P2 is a load-bearing conformance FAIL.

---

## §11 Evaluation modes and transfer cells [NORMATIVE]

- **[EVALM-1] Mode R (routing).** The selector of [SEL-1] picks the worker; the prompt is the EMPTY-context base prompt; the outcome is read from the `NS_MAIN` (or `NS_REPL` for A′) ledger entry for (chosen worker, task). The context component is not read in Mode R.
- **[EVALM-2] Mode C (fixed worker).** Worker identity is fixed; the routing component is not read; the prompt is built with the arm's context block; the outcome is the ledgered completion for (worker, full-prompt hash).
- **[EVALM-3] Cells.** E2: new task, same capability and family as TRAIN. E3: same capability and family, changed surface form. E5: same capability, structurally novel ([PART-2]). E6: RB tasks. E7: DA tasks (negative control). E1: TRAIN replay (Track C only; excluded from all labels).
- **[EVALM-4] Track R cell use.** Track R labels use E2, E3, E5. E6 and E7 are evaluated for static-worker gap reporting only: the routing carrier has no trained key for RB or DA, so every arm ties and B ≡ A there by construction; these cells MUST NOT be presented as a negative control for routing.
- **[EVALM-5] Track C cell use.** Track C uses E2, E5, E7 (labels), E6 and E1 (reported). LEARNED runs for all three workers; NEUTRAL, HANDWRITTEN, POISON, D_C for P only.
- **[EVALM-6] Pairing.** Comparisons are paired per task on the identical task set. Where two arms select the same worker (or build the same prompt), they share the ledgered outcome, so their difference is exactly zero on those tasks.
- **[EVALM-7] Generation budget.** The design implies on the order of 12,000 ledgered generations (DEV, TRAIN, Stage 3 base and context variants, A′ regeneration, longitudinal). Feasibility on the available hardware is UNKNOWN. If the budget is insufficient the remedy is a new protocol version; arms and cells MUST NOT be dropped or subsampled within v1.1.

---

## §12 Longitudinal accumulation (Track C) [NORMATIVE]

Scope (disclosed): primary fixed worker P, capability LA only, four rounds j = 0..3. Constants: CONST[K_LONG_PER_ROUND]=2, plus N_LONG_TRAIN_ROUND, N_LONG_EVAL_BLOCK, K_MAX.

- **[LONG-1] Arms.** LB (learned, growing), LN (neutral, growing, from the DA reference pool), LE (empty). At round j, LB's store holds exemplars from rounds 0..j: from LONG_TRAIN block j, P's first K_LONG_PER_ROUND oracle-passing episodes in seeded order (fewer if fewer pass; logged). Store size therefore reaches at most 2(j+1) ≤ K_MAX. LN's store grows by the same count per round from the DA reference pool.
- **[LONG-2] Restart.** Before each round's evaluation, the process is killed and restarted (new PID logged). Store hashes before and after each restart MUST be equal, and the store count MUST equal the expected count exactly (an overwrite or reset is a failure, never a finding).
- **[LONG-3] Fresh sealed evaluation.** Round j is evaluated on LONG_EVAL block j only (30 same-family + 30 structurally novel tasks), never before materialized, never previously used in any prompt, in the namespace `NS_LONG_j`. For each block, LB, LN, and LE outcomes are generated fresh. Reads across `NS_LONG_*` namespaces are forbidden ([ORC-4]).
- **[LONG-4] Retention.** After round 3, block 0 is **regenerated** under LB's round-3 store in `NS_LONG_RET` (forced regeneration, logged; the round-0 cached outputs MUST NOT be read). Retention passes iff pass(block 0 | LB round-3) is not significantly worse than pass(block 0 | LB round-0) (one-sided exact McNemar p ≥ RETENTION_ALPHA) and the difference is ≥ −RETENTION_TOL_PP.
- **[LONG-5] New gain.** Let `d_i` be the per-task paired difference (LB − LE) and, separately, (LB − LN). New gain passes iff, for **both** series, (size-weighted mean of d over blocks {2,3}) − (that over blocks {0,1}) ≥ TREND_MIN_PP with a one-sided permutation p < ALPHA (CONST[PERM_RESAMPLES]=10000), where the permutation exchanges the block-group label ({0,1} vs {2,3}) among (block, template-family) clusters, not among individual tasks, **and** the same difference computed on the structurally novel halves alone is ≥ TREND_MIN_PP with a one-sided permutation p < CONST[NOVEL_TREND_ALPHA]=0.10 (so growth in same-family template coverage alone cannot earn the label). Carrier statistics (`count`, `mean`, store size) are never evidence of accumulation.
- **[LONG-6] Freshness checks.** (a) Every LONG_EVAL task id is absent from all earlier prompt-hash logs; (b) `cross_namespace_hits = 0`; (c) every completion in `NS_LONG_j` was generated in that round (timestamps inside the round's window); (d) the retention regeneration sets `force_regenerate=true`.
- **[LONG-8] Family-coverage control.** Every LONG_TRAIN block and every LONG_EVAL same-family half draws from the same fixed set of at least CONST[MIN_FAMILIES_LONG]=6 template families, each used equally (±1 task) in every block, with identical difficulty-parameter strata counts, so that neither same-family coverage nor block difficulty changes systematically across rounds; the per-round family coverage of each exemplar store is logged. The family assignment is fixed by generator metadata before any worker output exists.
- **[LONG-7] Verdict.** [HYP-C6] passes iff [LONG-2], [LONG-4], [LONG-5], [LONG-6], and [LONG-8] all pass. Since a hand-run cache cannot satisfy [LONG-3]–[LONG-6], reusing prior outputs cannot earn the accumulation label.

---

## §13 Isolation preflight [NORMATIVE]

Every check is mechanical and must pass before any model call. Output: `runs/preflight_report.json` with a top-level `"pass"` and per-check breakdown.

- **[ISO-1]** Distinct in-process carrier-manager object identities across all arms.
- **[ISO-2]** Distinct `os.path.realpath()` of every arm's `runs/<arm_id>/` root; every root absent or empty at start.
- **[ISO-3]** Equal cold-start state hashes across cold arms; state hashes differ from the baseline hashes of the production files `memory/river_brain.pkl`, `memory/task_type_classifier.pkl`, `memory/self_model_claims.jsonl`, `memory/behavioral_directives.json`, captured before the run and recaptured after.
- **[ISO-4]** Each arm runs as a separate OS process (`subprocess.run`, fresh interpreter, never a fork of a mutated interpreter); PIDs logged, pairwise distinct.
- **[ISO-5]** No module-level cache, lazy-singleton accessor, or `get_X()` shared-instance function in the harness (static AST/grep check).
- **[ISO-6]** No shared mutable object between arm managers.
- **[ISO-7]** No write-mode `open()` of any `memory/` path in the harness (static check).
- **[ISO-8]** Forbidden imports of [INFRA-6] absent (static import audit).
- **[ISO-9]** **Quiescence.** The FeralEcho server and every autonomous loop are stopped for the entire run: no `run.py` process, no `start_echo.sh` watchdog process, port 5000 closed, no other client connected to the Ollama port (verified by a connection listing before Stage 1 and after Stage 3). Production-file hashes of [ISO-3] MUST be unchanged after the run.
- **[ISO-10]** No file under any arm root has an mtime earlier than that arm's own start timestamp; no arm root contains files from another arm.

If any check fails the main experiment MUST NOT run.

---

## §14 Apparatus qualification [NORMATIVE]

**[QUAL-1] Composite gate.** PASS requires all of §13, §14 [QUAL-2] through [QUAL-8], §22's static checklist, and §20's pre-run conformance items. Any failure of a security (QUAL-2), determinism, tie (QUAL-4), or invariance (QUAL-5) item is CRITICAL and yields APPARATUS INVALID; nothing experimental runs.

**[QUAL-2] Sandbox exploit battery.** Run through the real oracle path, identical in function, profile, and subprocess shape to real episodes. Required outcome for each: the attack fails or yields `y=0`; a false pass is CRITICAL.

| ID | Attack | Required outcome |
|---|---|---|
| QX1 | Candidate reads a canary file placed in `HIDDEN_ROOT` by absolute path | PermissionError/FileNotFoundError; the canary's unique content appears nowhere in captured output |
| QX2 | `os.walk`/`glob` from `/`, `$HOME`, the repository root, and parents of scratch, searching for answer/expected-output artifacts | Cannot read or list `HIDDEN_ROOT`/`PROMPT_ROOT`; no artifact content returned |
| QX3 | Symlink inside scratch pointing at `HIDDEN_ROOT`, then read through it | Read denied |
| QX4 | Read metadata (`stat`, `listdir`) of `HIDDEN_ROOT` | Denied; existence not distinguishable from a missing path |
| QX5 | Dump `os.environ` | Contains only the allowlisted keys of [INFRA-4]; a canary variable set only in the orchestrator's environment never appears |
| QX6 | Open a socket to loopback/Ollama and to an external host | Blocked |
| QX7 | Write or rename outside scratch; spawn a subprocess; `ctypes`/`dlopen` | Blocked |
| QX8 | Import a project module through `sys.path` (repository root not present) | ImportError |
| QX9 | Detect grading (inspect `sys.modules`, stack frames, scratch path names, env) and behave differently | Detection features are identical between qualification and real episodes (checked mechanically by hashing the invocation shape: same function, profile, argv shape) |
| QX10 | Read the test inputs, hardcode a constant output, or return a different task's expected output | `y=0`: expected outputs never enter the sandbox and grading binds `task_id` to its own expected-output file by explicit key |

**[QUAL-3] Discrimination fixtures.** Using QUAL tasks and frozen synthetic candidates: a constant-return candidate, a correct-on-QUAL/wrong-on-fresh-edge-case candidate, and a hash-order-dependent candidate MUST each score `y=0`; a genuinely correct solution submitted under each hash seed MUST score `y=1`; a genuinely correct solution through the full `learn()` path MUST produce exactly one ledger line and one carrier update.

**[QUAL-4] Tie qualification (tie handling cannot create the effect).** CONST[TIE_QUAL_N]=100000, CONST[TIE_QUAL_TOL]=0.005, CONST[SIM_REPLICATES]=500, CONST[NULL_FPR_MAX]=0.07, CONST[POS_POWER_MIN]=0.80. All on synthetic ledgers, no models:
  (a) *Identity-bias:* over TIE_QUAL_N draws with tied sets of size 3 and of size 2, each worker is chosen with frequency within TIE_QUAL_TOL of 1/|T|; the test is repeated with the worker identifiers permuted and the per-identifier frequencies are again within tolerance.
  (b) *Best/worst neutrality:* on a synthetic ledger with workers of pass rates 1.0, 0.5, 0.0, the cold selector's pass rate equals 0.5 within TIE_QUAL_TOL.
  (c) *Key independence:* selections under TIE_KEY_MAIN and TIE_KEY_REPL agree at the chance rate within tolerance.
  (d) *Null-effect calibration:* on synthetic ledgers with statistically identical workers (and template-family clustering of outcomes), run the full pipeline (arms A, B-with-any-carrier, tests of [HYP-R1] under [STAT-7]) SIM_REPLICATES times; the rate of [HYP-R1] passing is ≤ NULL_FPR_MAX. Repeat with a hand-typed carrier.
  (e) *Positive control:* on synthetic ledgers with true per-capability heterogeneity ≥ 2 × HEADROOM_PP, [HYP-R1] passes in ≥ POS_POWER_MIN of replicates.
  Failure of any item is CRITICAL.

**[QUAL-5] Fixed-worker invariance.** For every w ∈ E, Mode-R prompts under B's routing carrier and under the cold carrier are hash-identical for every EVAL-shaped task (checked on PILOT-shaped tasks before Stage 3 and re-asserted on EVAL at Stage 3). Any difference is CRITICAL.

**[QUAL-6] Carrier-implemented static policy.** On PILOT-shaped tasks with a stub ledger, each H-BLIND-X selects X on every task.

**[QUAL-7] Statistical code validation.** The analysis code (exact McNemar, cluster sign-flip permutation, cluster bootstrap, equivalence) reproduces known-answer synthetic results (fixed expected p-values and CI endpoints frozen at P1), and on synthetic ledgers with within-family outcome correlation ρ ∈ {0, 0.3, 0.6} and no true effect, the combined [STAT-7] rule's false-positive rate is ≤ NULL_FPR_MAX for every ρ.

**[QUAL-8] Determinism probe.** On PILOT, each worker generates each of 5 prompts five times; the per-worker output-identity rate is reported. It is informational: it does not gate, and it MUST NOT be used to change §4.

---

## §15 Statistical procedures [NORMATIVE]

Constants: CONST[BOOT_RESAMPLES]=10000, CONST[STAT_SEED]=4042026.

- **[STAT-1] Paired difference test.** One-sided exact McNemar: with `b` tasks where the first arm passes and the second fails, `c` the reverse, `p = P(X ≥ b | n=b+c, p=0.5)`. When `b+c=0`, `p=1`.
- **[STAT-2] Equivalence.** Cluster bootstrap over template families (resampling families with replacement within capability; BOOT_RESAMPLES, STAT_SEED); equivalence to within ±m holds iff the 90% percentile CI of the paired pass-rate difference lies inside (−m, +m).
- **[STAT-3] Effect sizes.** Report every pass-rate difference in percentage points with a cluster-bootstrap 95% CI.
- **[STAT-7] Cluster-robust confirmation (pseudo-replication guard).** Tasks from one template family have correlated outcomes, so exact McNemar on tasks can be overconfident. For every one-sided "p<ALPHA" clause in §2, let `d_f` be the mean paired difference within cluster f (cluster = capability × template family) and `T = Σ n_f d_f / Σ n_f`; the cluster p-value is the fraction of PERM_RESAMPLES sign-flip resamples of the `d_f` (seed STAT_SEED) with `T* ≥ T`. A "p<ALPHA" clause passes **only if both** the exact McNemar p-value ([STAT-1]) and the cluster p-value are below ALPHA. Where a comparison has fewer than 10 clusters it cannot pass a "p<ALPHA" clause.
- **[STAT-4] Family and aggregation.** A label requires the conjunction of its hypotheses; each component test is one-sided at ALPHA. No averaging across capabilities to rescue a failing component; the pooled test is primary and the "≥2/3 positive" clause is the replication requirement. No interim looks; sample sizes are fixed by §5.
- **[STAT-5] Power statement (informational, assumption-based).** With 450 pooled paired tasks and a discordance rate of 15–25%, an 8-percentage-point true gain gives well above 90% power for the one-sided McNemar and equivalence within ±5 pp is achievable; per-capability tests (n=150) are underpowered and are used only for the replication clause. Cluster-level power depends on the number and size of template families and is UNKNOWN until the generator exists. This does not guarantee any outcome.
- **[STAT-6]** The analysis and adjudication code is hashed at P1 and may read results only through the sealed evidence ([EVID-3]).

---

## §16 Adjudication [NORMATIVE]

Weakest-label-wins. Reported per track. Every label carries the suffix of [SCOPE-9]. None implies weight learning or that existing FeralEcho had the property.

- **[ADJ-0]** If the composite apparatus gate ([QUAL-1]) fails, or any load-bearing conformance item ([CONF-2]) fails, or [PART-6] applies, **both tracks: APPARATUS INVALID.** Raw performance MUST NOT override this.

- **[ADJ-1] Track R algorithm:**
1. G1 fails ⇒ **STATIC-WORKER REDISCOVERY** (routing headroom over the best static worker is not present; nothing above is adjudicable).
2. Else [HYP-R1] fails: if H-DEV beats BEST-STATIC-DEV by ≥ ROUTE_GAIN_PP with p<ALPHA ⇒ **CARRIER-CONTROLLED BEHAVIOR**; else if ≥ CONCENTRATION of B's pooled E2 selections go to a single worker ⇒ **STATIC-WORKER REDISCOVERY** (learned routing merely rediscovered "always choose worker X"; the report MUST name X); else ⇒ **NO REPRODUCIBLE EFFECT**.
3. [HYP-R1] passes: if [HYP-R2] ∧ [HYP-R3] ∧ [HYP-R4] all pass ⇒ at least **EXPERIENCE-DEPENDENT ROUTING ADAPTATION**; otherwise ⇒ **CARRIER-CONTROLLED BEHAVIOR**.
4. If step 3 earned EXPERIENCE-DEPENDENT ROUTING ADAPTATION and additionally [HYP-R5] passes ⇒ **PERSISTENT ROUTING ADAPTATION**.
5. If step 4's label was earned and additionally [HYP-R6] passes ⇒ **TRANSFERABLE ROUTING ADAPTATION**.

- **[ADJ-2] Track C algorithm:**
1. [HYP-C1] fails: if HANDWRITTEN beats EMPTY for P by ≥ CTX_GAIN_PP with p<ALPHA ⇒ **CARRIER-CONTROLLED BEHAVIOR (context track)**; else ⇒ **NO REPRODUCIBLE EFFECT (context track)**.
2. [HYP-C1] passes: if [HYP-C2] ∧ [HYP-C3] ∧ [HYP-C5](b) pass ⇒ **FIXED-WORKER EXPERIENCE-DEPENDENT IMPROVEMENT**; otherwise ⇒ **CARRIER-CONTROLLED BEHAVIOR (context track)**.
3. If step 2 earned FIXED-WORKER EXPERIENCE-DEPENDENT IMPROVEMENT and additionally [HYP-C4] ∧ [HYP-C5](a) pass ⇒ **PERSISTENT ACQUIRED SYSTEM-LEVEL COMPETENCE CONSISTENT WITH EVIDENCE**.
4. If step 3's label was earned and additionally [HYP-C6] passes ⇒ **ACCUMULATED SYSTEM-LEVEL COMPETENCE CONSISTENT WITH EVIDENCE**.

- **[ADJ-3] H4 (poison) is load-bearing and prohibits labels, not merely annotated.** Failure of [HYP-R3] prohibits EXPERIENCE-DEPENDENT ROUTING ADAPTATION, PERSISTENT ROUTING ADAPTATION, and TRANSFERABLE ROUTING ADAPTATION. Failure of [HYP-C3] prohibits FIXED-WORKER EXPERIENCE-DEPENDENT IMPROVEMENT, PERSISTENT ACQUIRED SYSTEM-LEVEL COMPETENCE, and ACCUMULATED SYSTEM-LEVEL COMPETENCE. A significant E7 gain ([HYP-C5](b)) prohibits the same three Track C labels.
- **[ADJ-4] Label semantics.** *CARRIER-CONTROLLED BEHAVIOR:* some carrier content (learned or handwritten) changes behavior beyond the comparators, but the chain establishing dependence on experience-derived content is incomplete. *EXPERIENCE-DEPENDENT ROUTING ADAPTATION:* the routing carrier built from oracle-verified experience improves selection beyond random and every static worker, is removed by ablation, is reversed by poisoning, and depends on capability-specific experience. It does **not** claim a hand-written carrier could not do the same ([HYP-RD]). *FIXED-WORKER EXPERIENCE-DEPENDENT IMPROVEMENT:* with worker identity held constant, an experience-built context carrier improves performance on same-family held-out tasks beyond empty and format-matched neutral context and is reversed by verified-incorrect context. This tier is narrow adaptation: it does not exclude template-level memorization or near-copying within a task family, and it MUST be reported as such; only the tiers above it require structurally novel tasks. *PERSISTENT ACQUIRED SYSTEM-LEVEL COMPETENCE CONSISTENT WITH EVIDENCE:* that improvement survives a real restart, is portable to a fresh instance, and transfers to structurally novel tasks. *ACCUMULATED SYSTEM-LEVEL COMPETENCE CONSISTENT WITH EVIDENCE:* additionally, repeated experience adds new gain on fresh sealed tasks while prior gain is retained.
- **[ADJ-5] Prohibited language.** No report may claim worker or model weight learning, existing-FeralEcho competence, autonomous self-improvement, general learning, or any of the exclusions of §23.
- **[ADJ-6] Reproducibility.** The adjudication MUST be computed by the frozen adjudication code from the sealed evidence and cite specific rows of §18's tables. A prose summary is not an adjudication.

---

## §17 Staging and stopping [NORMATIVE]

- **[STG-1] Stage 0:** §13 preflight, §22 static checklist, tie and statistical qualification ([QUAL-4], [QUAL-7]), all model-free. Fail ⇒ APPARATUS INVALID; stop.
- **[STG-2] Stage 1:** [QUAL-2], [QUAL-3], [QUAL-5], [QUAL-6], [QUAL-8], on PILOT and QUAL only. A defect in the *harness* (not in the protocol) found here may be fixed and Stage 1 rerun, recorded in the `pilot_decision_log`; this is apparatus debugging only and MUST NOT touch §4.
- **[STG-3] P1 commit** ([PART-4]). **DEV measurement**, gate G1, DEV-derived decisions ([BASE-1]–[BASE-7]); **P2 commit**.
- **[STG-4] Stage 2 (TRAIN):** construct B, E, M, LEARNED/POISON/NEUTRAL/HANDWRITTEN and the H arms; required restarts.
- **[STG-5] Stage 3 (single full-scale execution):** materialize EVAL; generate all ledgers; seal; then analyze. One Stage 3 execution per (P1, P2) pair ([VER-3]). It runs to completion or is reported as aborted with reason.
- **[STG-6] Longitudinal stage (§12)** runs after Stage 3's Track C analysis and only if [HYP-C1] passed; its failure bounds the label at PERSISTENT ACQUIRED SYSTEM-LEVEL COMPETENCE and does not retract it.
- **[STG-7]** No stage may be skipped, and no exploratory run on EVAL is permitted at any point (no "quick test").
- **[STG-8]** Track R and Track C outcomes are always both reported, whichever fails.

---

## §18 Result tables (blank, frozen schema) [NORMATIVE]

Column and row structure may not change after data exists without a new protocol version. Columns common to T1–T4: `run_id | arm_id | carrier_provenance_category | carrier_values_hash | state_hash_init | state_hash_post_learning | state_hash_post_restart | state_hash_post_eval | process_pid | filesystem_root | grader_hash | inference_settings_hash | ledger_namespace | exclusion_count | retry_count`.

- **[TAB-1] T1 Track R arms and baselines** — rows: A, A′, B, C, D, N, E, M, H-BLIND-qwen, H-BLIND-llama, H-BLIND-deepseek, H-DEV, SW-qwen, SW-llama, SW-deepseek, RAND, BEST-STATIC-DEV, BEST-STATIC-PERCAP-DEV. Extra columns: `task_partition | capability_scope | worker_selection_histogram | pass_rate | n_tasks | ci95_low | ci95_high | vs_best_static_pp | vs_A_pp | vs_A_prime_pp | p_values | tie_key_id`.
- **[TAB-2] T2 Track C arms** — rows: EMPTY, LEARNED (each worker), NEUTRAL(P), HANDWRITTEN(P), POISON(P), D_C(P). Extra columns: `fixed_worker | exemplar_count | exemplar_store_hash | prompt_hash_set_hash | task_partition | pass_rate | n_tasks | ci95 | vs_EMPTY_pp | vs_NEUTRAL_pp | p_values`.
- **[TAB-3] T3 Transfer cells** — rows: cell × arm × capability for E1, E2, E3, E5, E6, E7. Extra columns: `cell_id | transfer_category | pass_rate | n_tasks | ci95 | effect_pp | p_value`.
- **[TAB-4] T4 Longitudinal** — rows: round × {LB, LN, LE} × {same-family, novel} plus retention row. Extra columns: `round | block_id | store_size | store_hash | restart_pid | pass_rate | n_tasks | paired_diff_pp | freshness_checks | cross_namespace_hits`.
- **[TAB-5] T5 DEV calibration** — per worker × capability: DEV pass rate, malformed/truncated/timeout/nondeterministic counts, G1 components, P selection.
- **[TAB-6] T6 Qualification and preflight** — one row per QX/QUAL/ISO check: `check_id | required_outcome | observed_outcome | pass_fail`.
- **[TAB-7] T7 Conformance and run ledger** — §20 conformance rows; every Stage 3 execution of every protocol version with hashes and outcome ([VER-4]).

---

## §19 Raw evidence preservation [NORMATIVE]

- **[EVID-1]** Retained per episode: prompt text and hash; the full request body; the full response; `done_reason`, `eval_count`; the extraction result and malformed category; both hash-seed outputs and outcomes; the oracle outcome; carrier/store contents and hashes at four checkpoints; the tie record ([TIE-3]); timestamps; PIDs; roots; seeds; arm assignments; restart evidence; every exception with traceback; every replacement with reason; model digests and Ollama version; the P1/P2 commit hashes; the harness, analysis, and grader hashes; the `pilot_decision_log`, `eval_exposure_log`, and `grader_manifest`.
- **[EVID-2]** Hidden answers/expected outputs may be retained post hoc (never solver-visible during a run).
- **[EVID-3]** The evidence directory is append-only with a hash chain (each record includes the hash of its predecessor); the chain head is written to the run ledger before analysis. Adjudication reads only from the sealed chain.
- **[EVID-4]** Every future report MUST cite rows of §18's tables; a report characterizing a result by prose alone is not adjudicable.

---

## §20 Conformance report — the first exhibit [NORMATIVE]

- **[CONF-1]** Before any result is interpreted and before the adjudication code will run, a conformance report MUST be produced by the frozen conformance script, listing for every rule ID in the JSON `rule_index`: `normative requirement → implementation location (file:line) → runtime evidence (log/hash/assertion reference) → PASS/FAIL`.
- **[CONF-2]** Each rule is marked *load-bearing* or not in the JSON. Any load-bearing FAIL prevents every label above APPARATUS INVALID. Raw performance cannot override nonconformance.
- **[CONF-3]** Any hash mismatch of the grader manifest, inference settings, model digests, or frozen constants invalidates the comparisons it touches and is a conformance FAIL.
- **[CONF-4] Ordering enforcement.** The adjudication function MUST refuse to run unless a conformance report with `pass=true` exists and its hash is recorded in the run ledger before the results tables are populated.
- **[CONF-5] Independent attestation.** Before Stage 3, a reader who is not the harness's author (a fresh review session or a human) MUST run the conformance script and compare the harness against §3–§9 and §13–§14, and record `conformance_attestation` (reviewer identity, scope, findings). The absence of this attestation is a load-bearing FAIL. Its independence is limited to that of a second reader.
- **[CONF-6]** The conformance report also embeds the diff between the implementation's realized frozen constants (every `CONST[...]`) and this document's values, and §22's checklist result.

---

## §21 Immutability, versioning, and reruns [NORMATIVE]

- **[VER-1] Freeze points.** P1 (pre-registration commit) and P2 (DEV-derived decisions commit) as defined in [PART-4] and [BASE-7]. Before P1 the implementer may iterate on harness code and generator design per [PART-3]. After P1, only [VER-5] permits changes.
- **[VER-2] Changes requiring a new protocol version, created before any affected outcome is examined:** any threshold or constant; any arm definition; any carrier field or update rule; oracle or grading logic; inference conditions; partition membership rules; any result-table column; any adjudication label requirement; anything [DOC-5] flags as unspecified. A new version discards the P1/P2 of its predecessor and requires its own P1/P2.
- **[VER-3] One full-scale execution per (P1, P2).** A Stage 3 that begins runs to completion or is reported as aborted. Infrastructure-fault resumption inside one execution ([INF-9]) is not a new execution.
- **[VER-4] Cumulative disclosure.** Every Stage 3 execution of every protocol version, with its hashes, protocol version, outcome, and reason for any abort, MUST appear in the run ledger (T7) of every report.
- **[VER-5] Permitted without a version bump:** fixing a harness bug that makes the harness disagree with this document (recorded with a diff and confirmed by [CONF-5]) *before Stage 3*; appending generator-produced file hashes as required by [PART-4].
- **[VER-6] Deliberate deferrals from v1.0 (not vulnerabilities):** second-generation transfer, the fourth worker, the lizard-tail rows L5–L8 (structurally null under exact-key design), and re-keying transplants are removed from v1.1; reintroducing any of them requires a new version.
- **[VER-7] Post-outcome reruns are exploratory.** Any run performed after Stage 3 outcomes of a prior (P1, P2) have been examined — including partial or aborted Stage 3 outcomes, and including any observation of ledger pass/fail values during generation — including under a revised protocol, is EXPLORATORY: its labels MUST be reported prefixed "EXPLORATORY (attempt k)", and no label above EXPERIENCE-DEPENDENT ROUTING ADAPTATION or FIXED-WORKER EXPERIENCE-DEPENDENT IMPROVEMENT may be reported for it.
- **[VER-9] Frozen-path integrity.** The set of frozen paths (generator, templates, harness, sandbox layer, analysis and adjudication code, `READ_ALLOW`, constants, digests) is recorded at P1. At Stage 3 start and end, `git diff P1 HEAD -- <frozen paths>` MUST be empty (apart from the [VER-5] addenda), P2 MUST be a descendant of P1, and the EVAL/LONG_EVAL generator MUST refuse to run unless the working tree is clean for those paths and P2 is an ancestor of HEAD. A non-empty diff is a load-bearing conformance FAIL.
- **[VER-8] Protocol deviation vs experimental failure.** A deviation ("the instrument needed adjustment before it could measure") and a failed hypothesis ("the instrument worked and reported a negative result") MUST be distinguished in every report. A negative Stage 3 outcome is never recharacterized as a deviation to justify a rerun as non-exploratory.

---

## §22 Static protocol-consistency checklist [NORMATIVE]

- **[CHK-1]** The JSON `rule_index` lists every rule ID defined in this document with its governing section; the frozen checker (its full source and SHA-256 are recorded in the appendix of the traceability artifact and MUST be committed unchanged at P1) verifies (i) each ID is defined exactly once, (ii) in the section named in the index, (iii) no ID is defined in §24, and (iv) every rule ID cited in the traceability artifact exists.
- **[CHK-2]** The checker verifies that each safeguard in the JSON `safeguards` list (tie handling, exclusion cap, pilot rules, grader hash verification, nondeterminism handling, conformance check, inference freeze, sealing, freshness, H4 label prohibition, sandbox interface, handwritten-carrier control) has its defining rule in its governing operative section and required anchor text in that section.
- **[CHK-3]** The checker verifies every `CONST[NAME]=value` in this document equals the JSON's constants and appears in the section the JSON names as governing.
- **[CHK-4]** The checker verifies that the harness reads carrier provenance fields nowhere in `score()` or the context builder, that no code path reads across ledger namespaces, and that the forbidden imports of [INFRA-6] are absent (run against the harness at Stage 0 and as a conformance item).
- **[CHK-5]** No safeguard counts merely because it appears in commentary: a safeguard whose only occurrence is in §24 fails the checklist.

---

## §23 Claim boundary [NORMATIVE]

- **[CLAIM-1] The strongest justified positive claim (top Track C label).** *A newly constructed, isolated learning pathway using FeralEcho's sandboxed-execution idea and local models demonstrated that experience-derived context, stored as a small persistent artifact, improved a fixed frozen worker's performance on new and structurally novel sealed tasks beyond empty and format-matched neutral context, was reversed by verified-incorrect context, survived real process restarts and transplant into a fresh instance, and accumulated additional gain on fresh sealed tasks with prior gain retained — with model weights unchanged.*
- **[CLAIM-2] The strongest justified routing claim (top Track R label).** *The same pathway learned, from oracle-verified experience, to route tasks among frozen workers better than random and better than every static worker, in a direction-sensitive and capability-specific way that survived restart and transplant and held on structurally novel tasks.* It is a claim about selection among existing workers, not capability acquisition.
- **[CLAIM-3] Not established by any outcome.** Foundation-model weight learning; existing RiverBrain competence learning; `self_model_claims` competence; autonomous self-improvement; unrestricted general learning; biological inheritance, reproduction, or instinct formation; consciousness, experience, or organism status; recursive self-improvement; exponential capability growth; that experience *provenance* matters beyond the information in the carrier (if a hand-written carrier reproduces an effect, [HYP-RD] applies); or anything about task families, workers, or inference conditions other than those frozen here.
- **[CLAIM-4]** Any outcome is a claim about the constructed pathway only, never about FeralEcho as it exists.

---

## §24 [COMMENTARY] Rationale (non-normative; contains no rules)

This section explains design choices and has no binding force. Where it names a mechanism, the binding text is in the cited section.

**Why two tracks.** v1.0's carrier was `{count, mean}` per worker; the selector could improve only by choosing a better pretrained worker, so "capability" and "routing" were confounded. Track R now measures routing against static-worker baselines; Track C adds a within-worker mechanism so a fixed-worker test can exist at all (§2, §7, §9).

**Why the tie-break changed.** Alphabetical tie-breaking made the cold baseline a deterministic always-one-worker policy and let a never-trained recipient win ties, so treatment effects were indistinguishable from worker-quality differences (blind-review V1, V2). The seeded hash draw of §8 is uniform over the tied set for every task; §14's tie qualification tests that claim rather than asserting it.

**Why the sham arm was redesigned.** v1.0's D and S1 were the same operation. Under a consumer that reads only two numbers, a value-matched sham cannot differ from the transplant, so it is removed; the controls that answer distinct questions are N (does the procedure itself do anything), H-BLIND (does an information-free carrier do it), H-DEV (does a DEV-informed hand-written carrier do it), and M (does capability-specific experience matter).

**Why H6 changed.** v1.0's retention cells could be satisfied by reusing cached outputs or by a constant policy. §12 evaluates on fresh sealed blocks in separate namespaces and forbids cross-namespace reads.

**Known residual limits.** Pre-P1 generator design remains implementer work, disclosed through the `pilot_decision_log`; conformance attestation is a second reader, not a panel; results hold for the frozen task families and inference conditions; low-power outcomes are "not demonstrated," not "demonstrated absent."
