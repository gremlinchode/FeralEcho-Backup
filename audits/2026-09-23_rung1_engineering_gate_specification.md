# Rung-1 Engineering-Gate Specification: Trusted Evaluator + Generation Accounting

Read-only. Git HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce` unchanged before and after (confirmed by direct `git rev-parse` before and after this investigation). Nothing was implemented, no evaluator was repaired, no selector was built, no trial was run. Only this report was created.

**Reconciled against**: `audits/2026-09-23_rung1_final_preimplementation_gate.md` (Codex, the document under specification here), and every predecessor this session (`audits/2026-09-22_preregistered_persistent_routing_experiment_design.md`, `audits/2026-09-22_persistent_learning_experiment_premortem.md`, `audits/2026-09-23_trusted_boundary_reconciliation.md`, `audits/2026-09-23_adversarial_learner_game.md`). Where feasible in the time available, claims were re-verified against source directly rather than relayed — two fresh checks were made specifically for this mission: `stream_query_ollama()`'s actual parameter list (confirmed: no seed parameter) and `app/experiments/accumulation_probe/ollama_client.py`'s actual content (confirmed: a real, already-functioning, seeded, metered, zero-production-import HTTP adapter — a meaningfully de-risking finding beyond what Codex's own text credits it for).

## 1. Executive verdict

**ENGINEERING-GATE is the correct verdict, independently confirmed, and this document moves the project to SPECIFICATION-READY — not READY-FOR-APPARATUS, since nothing has been built.** The scientific question (Rung 1: does independently evaluated experience causally, persistently, and fairly improve later strategy selection) is fully specified after Codex's final gate resolved the two remaining ambiguities — the task-information contract (every worker now gets the complete task specification, including any local convention, removing convention-induction from scope) and the template-only-arm question (unnecessary; folded into champion-candidate selection instead). What remains is concrete engineering: a trusted evaluator boundary that does not exist yet in any qualified form, and a generation-accounting layer that does not exist yet in any qualified form. **One material, independently-verified finding beyond Codex's own text**: AP-0's existing `ollama_client.py` is not merely "a useful source pattern" for the generation adapter — it already implements most of the required seed/metering/no-implicit-fallback contract as working code, meaningfully lowering the engineering cost of that half of the gate. The evaluator-boundary half remains the larger, genuinely new piece of work.

## 2. Final-gate reconciliation

**Why Codex selected ENGINEERING-GATE rather than the three alternatives, independently checked, not merely summarized:**

- **Not THEORY-NOT-DONE**: the final bounded claim (§3 there), the excluded-claims list (§4), the three required arms with the template-only question resolved (§5, §12), the causal chain (§6), and the complete state manifest (§7) leave no unresolved question about *what* Rung 1 means or *what* would count as establishing it. Independently checked: I find no gap in this reasoning. The template-only resolution specifically holds up under its own logic — Codex's worked example (hold a K1 task's morphology and status token fixed while assigning that token to different categories across two possible worlds; a template recognizer with no convention information cannot solve both) is a real, valid demonstration that pure structural-template recognition cannot substitute for the convention information every worker is now given identically. **This directly supersedes my own prior proposal for a fourth, information-denied template-only arm** (`audits/2026-09-23_adversarial_learner_game.md` §9) — accepted here per the mission's own explicit instruction not to reopen it absent new evidence, and none was found.
- **Not READY-FOR-APPARATUS**: independently re-confirmed (§5/§8 of this report) — the evaluator remains the same-module-access architecture found and confirmed repeatedly across this session; neither `_ollama_query()` nor `stream_query_ollama()` satisfies the seeded, single-call, fully-metered, no-implicit-fallback contract; no state manifest, restart controller, or champion-selection procedure has been built.
- **Not NOT-FEASIBLE**: nothing found across any of this session's five prior investigations, or this one, shows the target phenomenon to be unmeasurable in principle — only that the tooling to measure it does not exist yet in qualified form.

**Every remaining prerequisite from Codex's §21, independently classified:**

| Prerequisite (Codex §21) | Classification | Independent verification |
|---|---|---|
| 1. No qualified expected-answer/process/filesystem/output-protocol boundary exists | **BLOCKING** | Re-confirmed directly this session (and twice before): `oracle_runner.grade()` + `tasks.py::make_test_code()` place `_CASES` in the same executed module as candidate code; `echo_sandbox.sb` allows unrestricted file reads; `jail.py`'s read-deny is scoped to the experiment root only |
| 2. Neither generation helper satisfies the seeded/single-call/metered/isolated contract | **BLOCKING, but materially de-risked** | Re-confirmed `stream_query_ollama()`'s signature has no `seed` parameter this session; **newly confirmed** `app/experiments/accumulation_probe/ollama_client.py` already implements a seeded (`"seed": seed` in the request body), metered (`eval_count`/`prompt_eval_count`/`total_duration`/`done_reason` all captured), zero-production-import, zero-implicit-fallback direct HTTP client — this is closer to "adopt and extend a ~20-line existing file" than "build a new adapter from nothing" |
| 3. Task packet/strategy/feature-granularity/state-schema choices need freezing | **BLOCKING, but sequenced after 1/2** — this is Stage 3 work (§23), not evaluator/generation engineering |
| 4. Controller-owned actor/artifact binding, state checkpoints, restart, diagnostics specified but not built | **BLOCKING**, sequenced after 1/2/3 as Stage 4 |
| 5. No champion, routing-opportunity evidence, pilot variance/cost estimates, thresholds, history count | **BLOCKING, but this is Stage 5 development/pilot work**, correctly out of scope for an *engineering* specification per the mission's own scope discipline |
| 6. Task/partition separation, oracle contract coverage, protected-diagnostic/holdout access need qualifying on the new substrate | **BLOCKING**, scoped to Stage 3's own new research task adapter, not to AP-0 itself, which is correctly never touched |

No item is **RESOLVED** yet, and none is merely **CLAIM-LIMITING** or **NON-BLOCKING** — every one of Codex's six items gates something real. The two the mission specifically asks this document to specify (items 1 and 2) are addressed in full below; items 3-6 are named, sequenced, and explicitly deferred to their correct later stage rather than specified here, per the mission's own scope discipline against redesigning FeralEcho or reopening Rung 2/theory questions.

## 3. Blocking prerequisites

Consolidated to the two named engineering gates this mission asks to specify, plus the four downstream items correctly excluded from this document's own scope:

**BLOCKING, specified in full here**: (A) Trusted evaluator isolation (§4-§9, §21 acceptance tests 1-4, 7-10). (B) Generation accounting (§10-§16, §21 acceptance tests 5-6).

**BLOCKING, correctly deferred to later stages, not specified here**: task-packet/menu/feature-granularity freezing (Stage 3); state-manifest implementation and restart controller (Stage 4); champion-selection development and pilot sizing (Stage 5).

## 4. Trusted evaluator invariant

**The exact invariant the repaired evaluator must satisfy**: *untrusted candidate execution must never have addressable access to protected expected outputs, hidden test structures, scoring internals, other protected candidates' cases, or researcher-only diagnostics — under any code the candidate can write, including code that assumes full knowledge of this very specification.*

- **Trusted controller** owns: the frozen task specification (where protection is required — see §3 of Codex's gate, which correctly narrows this to hidden expected outputs and test cases only, since the task's own public specification and convention are now given to every worker identically), expected outputs, hidden test cases, scoring logic, protected randomness (none required for AP-0-shaped pure-function grading, but reserved for future use), and rich diagnostics. It sends only permitted task inputs across the boundary — never test-authoring code, never a prior case's result, never any protected byte.
- **Untrusted candidate process** receives only the candidate's own source and one permitted input per invocation (§8's per-case granularity decision). It returns only a constrained, typed, size-bounded output (§9) and nothing else the controller trusts.
- **Trusted comparison** occurs strictly after the untrusted process has run and exited, inside the controller's own process, comparing its own independently-held expected value against the parsed (never executed, never `eval`'d) candidate output.

## 5. Current evaluator failure

Re-confirmed directly this session (fourth independent confirmation across the 2026-09-22/23 report sequence, not merely inherited): `oracle_runner.grade()` (`app/experiments/accumulation_probe/oracle_runner.py:41-48`) concatenates candidate code with `make_test_code()`'s output; `make_test_code()` (`app/experiments/accumulation_probe/tasks.py:246`) writes `_CASES = [(args, expected), ...]` as a bare module-level global into that same script, and its generated test loop **deliberately prints** the failing `(args, actual, expected)` tuple on mismatch. `echo_sandbox.sb` (the profile `oracle_runner.py` actually invokes for grading) contains `(allow file-read*)` with no scope restriction. `jail.py` (AP-0's *generation*-arm sandbox, a different profile) denies reads only within the experiment root, not the general filesystem.

**One precise engineering point this session adds explicitly, not previously stated this sharply**: removing `_CASES` from the concatenated script's *namespace* is necessary but not sufficient on its own — if the expected values still exist anywhere the candidate's own sandbox profile can read (a scratch file, an inherited file descriptor, a sibling readable path), a namespace-only fix accomplishes nothing. The repair must close the *data-access boundary*, not merely rename or relocate the variable.

## 6. Minimum process-isolation design

**Trusted parent (controller) → isolated child (candidate, one per test case) → output serialization → trusted comparison**, reusing the existing sandbox-exec mechanism, restructured rather than replaced:

1. The controller writes the candidate's source alone (no test code, no `_CASES`) to a fresh, per-case scratch file.
2. The controller launches a new `sandbox-exec` subprocess against a **new, research-owned sandbox profile** (not `echo_sandbox.sb`, not `jail.py`) whose default posture is `(deny file-read*)` with narrow, explicit allows: the candidate's own scratch file, and the minimal Python interpreter/stdlib paths actually required to run — a materially tighter posture than either existing profile, neither of which was built for this purpose. Network is explicitly denied (reusing `echo_sandbox.sb`'s own precedent, not `jail.py`'s, since `jail.py` leaves networking open). Process-fork/exec is explicitly denied (reusing `echo_sandbox.sb`'s own documented precedent). The child's inherited environment is sanitized to an explicit minimal allowlist — neither existing profile does this today (`jail.py`'s `run_jailed()` passes the full parent environment unfiltered, confirmed by direct read). File descriptor 0 is closed before candidate code runs, reusing `safe_exec_wrapper.py`'s own documented "Mission 29" precedent as a template, not by importing that file.
3. The subprocess is invoked with exactly one permitted input (serialized, e.g., as a single JSON argument or via stdin) and is expected to print exactly one typed, bounded output value to stdout — nothing else. It never receives `_CASES`, an expected value, or any prior case's outcome.
4. The controller, running entirely outside this subprocess and its sandbox, reads only the subprocess's stdout, parses it strictly (§9), and performs the comparison against its own separately-held expected value **after** the subprocess has exited.

**Reuse assessment, prefer-reuse-first as instructed**: the underlying `sandbox-exec` invocation shape (`oracle_runner.run_script()`'s own pattern) and `safe_exec_wrapper.py`'s fd-closing/output-parsing conventions are directly reusable as *templates*; the profile itself and the per-case (not per-suite) invocation shape are genuinely new, research-only artifacts — matching Codex's own explicit statement that this is "a new research evaluator adapter/profile, not an edit of `oracle_runner.py`, `safe_exec_wrapper.py`, or the production sandbox," and matching this project's own established precedent (`oracle_runner.py`'s own docstring explains it deliberately reimplements `run_sandbox_script_isolated`'s invocation rather than importing it, for an analogous reason).

## 7. Perfect-information attack

Assuming the candidate knows the entire design above — every channel from the mission's list, classified:

| Channel | Classification | Reasoning |
|---|---|---|
| Globals | **CLOSED BY DESIGN** | Fresh process, fresh interpreter; expected values never enter the child's namespace at all |
| Frame inspection (`sys._getframe()` walking the call stack) | **CLOSED BY DESIGN** | A separate OS process cannot walk a parent process's Python call stack — this is precisely why process separation, not namespace separation, was chosen as the mechanism |
| Module inspection (introspecting its own module) | **IRRELEVANT** | Nothing sensitive exists in the child's own module |
| Imports | **REQUIRES EXPLICIT CLOSURE** | The narrow read-allowlist must restrict which stdlib/third-party modules are importable at all; the kernel-level network/fork/write denials close most escalation paths regardless |
| Filesystem access | **REQUIRES EXPLICIT CLOSURE** | The single most concrete, previously-open gap (§5) — must tighten beyond either existing profile's read posture |
| Environment variables | **REQUIRES EXPLICIT CLOSURE** | Confirmed real gap in `jail.py`'s current behavior; must sanitize to a minimal, explicit allowlist |
| Inherited file descriptors | **REQUIRES EXPLICIT CLOSURE** | Close fd 0 per existing precedent; explicitly verify no controller-side log/data handle is inherited via default subprocess fd behavior |
| Parent-process information | **UNKNOWN** | Whether macOS Seatbelt exposes parent/sibling-process metadata to a denied-by-default child was not independently tested this session — flagged honestly, not assumed closed |
| Process enumeration | **REQUIRES EXPLICIT CLOSURE, partially UNKNOWN** | Fork/exec denial is specifiable now; whether the same denial also blocks mere enumeration (e.g., a `ps`-equivalent syscall) needs a dedicated hostile-fixture check |
| Temporary files | **REQUIRES EXPLICIT CLOSURE** | Each case gets its own unique, never-reused scratch root; no case's child may read a path used by any other case |
| IPC | **REQUIRES EXPLICIT CLOSURE, partially UNKNOWN** | Deny beyond the bare minimum; the one already-accepted exception in the production sandbox (`(allow mach-lookup)` for ObjC/CoreFoundation runtime internals) may need the same acceptance here, but its use as a covert channel in this narrower context was not independently tested |
| stdout/stderr | **REQUIRES EXPLICIT CLOSURE — the single most important item** | This is exactly the channel `make_test_code()`'s own current design leaves wide open by printing failing input/actual/expected; the repaired design must accept **only** the one declared typed value and reject everything else as malformed |
| Exception messages | **REQUIRES EXPLICIT CLOSURE** | A raw traceback (which can include source lines or, in some tooling, local-variable reprs) must collapse to a coarse, pre-classified category, never raw text, before reaching the controller's decision logic |
| Networking | **CLOSED BY DESIGN, if explicitly denied** | Must be an explicit deny in the new profile — not assumed from either existing profile, since `jail.py` leaves it open |
| Deterministic seeds | **IRRELEVANT** | Not applicable to candidate-execution correctness-checking; relevant only to the generation side (§10-§17) |
| Timing | **REQUIRES EXPLICIT CLOSURE (for the learner) / bounded (for infra)** | The sandbox enforces a bounded runtime for infra reasons (timeout classification); the controller separately never exposes candidate timing to the learner (§11) |
| Serialization tricks (adversarial `__eq__`/crafted objects) | **CLOSED BY DESIGN** | The controller parses only a narrow, pre-declared primitive schema and never executes, `eval`s, unpickles, or imports anything from the candidate's output, and never invokes a candidate-supplied object's own comparison method |
| Multiple-test contamination | **CLOSED BY DESIGN** | Per-case execution (§8) — each case's child has no memory of, or access to, any other case |

## 8. Execution granularity

**Per-case execution is the correct minimum granularity, not per-suite (today's `grade()` shape) or per-task-ambiguous.** Tradeoffs, worked through rather than asserted: information leakage is strictly reduced (a per-suite child could in principle behave differently across cases within one long-lived process; per-case eliminates this categorically). State carryover is eliminated entirely by construction. Computational cost genuinely increases — N cases now means N subprocess/sandbox-exec spawns rather than one, and sandbox-exec startup overhead is real and non-trivial. Reproducibility improves (each case is a fully self-contained, independently replayable unit). Timeout attribution improves (a suite-level timeout cannot identify which case hung; a per-case timeout can). Candidate semantics: for AP-0-shaped pure, stateless functions, there is no legitimate reason a candidate would need shared setup or cross-case state — this is stated explicitly as a scoping assumption of *this* minimal design, not a universal claim about all possible task shapes. **Recommendation: per-case execution, accepting the real cost increase as the necessary price of the trust-boundary invariant.**

## 9. Candidate output contract

- **Type**: a single JSON-serializable primitive or small, fixed nested structure matching the task's own declared return-type contract; every task declares its exact expected shape (int/bool/tuple-as-list/dict-with-string-keys/etc.) in advance, at task-freeze time.
- **Serialization**: strict `json.loads` only — never `eval`, `pickle`, or dynamic import of anything the candidate returns.
- **Size/type limits**: a small, fixed byte cap (generous for AP-0-shaped small return values, e.g. a few KB) and a fixed maximum nesting depth; anything exceeding either is rejected as malformed before any comparison is attempted.
- **Type restrictions**: any JSON value not matching the task's declared type (e.g., a string where an int was contracted) is rejected as malformed, not coerced.
- **Timeout behavior**: a bounded CPU/wall-clock limit enforced by the sandbox subprocess itself; a timeout is a task failure under the declared contract (§20), never silently retried.
- **Malformed output handling**: parse failure, size/depth overflow, or type mismatch is a task failure, logged researcher-side under a coarse `malformed_output` category — never forwarded to the learner as diagnostic text.
- **Process crash handling**: a nonzero exit code or a sandbox-denial signal is also a task failure at the researcher-evidence level, and — critically — is classified identically to "ran fine but wrong answer" at the *learner-feedback* level (both are simply FAIL), while remaining separately distinguishable at the *researcher-evidence* level (§10) for debugging.

## 10. Researcher evidence contract

RESEARCHER_ONLY, stored in a private, append-only log the learner's own decision code has no code path capable of opening: stdout/stderr, full traceback, exit code, sandbox-denial detail, per-case timing/duration, per-case result detail, evaluator diagnostics of any kind. This mirrors Codex's own §9 table exactly and is adopted here without modification — three independent passes across this session (the trusted-boundary report, the adversarial-learner-game report, and Codex's own final gate) now agree on this contract, which is worth stating as convergent, cross-checked confidence rather than mere repetition.

## 11. Learner feedback contract

**PASS/FAIL alone is sufficient for Rung 1 — confirmed, for the third independent time this session, by a third independent report (Codex's own §9), converging with my own two prior reports' identical conclusion.** The precise minimal update tuple is `(feature_bucket, strategy_used, PASS_or_FAIL)` — but only the outcome bit is genuinely *new* information crossing the trust boundary; `feature_bucket` and `strategy_used` are the learner's own prior decision, echoed back to it, not evaluator-derived data. No richer field (timing, per-case detail, exception class) is justified for this rung, and none is added here.

## 12. Generation-path trace

Re-confirmed directly this session: `river_deliberation._ollama_query()` (`app/core/river_deliberation.py:397`) accepts `model_name, prompt, timeout, temperature, system, max_tokens, task_type` — **no seed parameter**. `app/ollama_handler.py::stream_query_ollama()` (line 421) accepts `prompt, persona, model, max_tokens, temperature, system, messages, result_meta` — **also no seed parameter**, confirmed by direct re-read of its own signature this session. Both therefore fail the "explicitly seeded" requirement outright, independent of the circuit-breaker/fallback issues already resolved in the trusted-boundary report. `_ollama_query()`'s streaming-exception fallback silently routes through a subprocess `ollama run` call with different system/temperature/token controls — confirmed, unchanged from the prior report's finding.

**New finding this session, materially changing the engineering-cost picture**: `app/experiments/accumulation_probe/ollama_client.py` — read in full for this report — is already a real, functioning, ~20-line direct HTTP client with **zero production imports**, that (a) explicitly sets `"seed": seed` inside its request `options`, confirming Ollama's `/api/chat` genuinely accepts a seed parameter this whole engineering gate needs; (b) captures `eval_count`, `prompt_eval_count`, `total_duration`, and `done_reason` from the real response — exactly the generation-event telemetry §14 below requires; (c) has no retry or fallback logic of any kind — a plain `requests.post` call, succeed or raise; (d) includes a separate `model_info()` function that queries `/api/tags` for the model's exact digest and `/api/version` for the Ollama server version. **This is not merely "a useful source pattern" (Codex's own framing) — it is a substantially complete implementation of the required client, needing adoption and light extension, not construction from scratch.** The one real, disclosed gap, correctly identified by Codex and independently confirmed by reading `model_info()`'s own implementation: it is a *preflight* check, called once, not a per-response attestation that the exact digest queried is the exact digest that served every later individual request — if the underlying model file changed mid-run, nothing in this client would detect it on a per-call basis.

## 13. Generation-state dependencies

| Channel | Classification (if reusing `_ollama_query()`) | Classification (recommended: dedicated adapter per §12) |
|---|---|---|
| RiverBrain | MUST BE ACCOUNTED (never called by `_ollama_query()` itself, but the surrounding harness must not accidentally instantiate it) | **ABSENT** — a plain `requests.post` adapter has no path to it at all |
| Council state, task classifier, attempt ledger, conversation memory, self-edit history | ABSENT (none of these are touched by `_ollama_query()`'s own body, confirmed by re-reading it this session and in the trusted-boundary report) | **ABSENT** |
| Circuit breaker (`_cb_state`) | **MUST BE ACCOUNTED** — real, in-memory, process-scoped, confirmed twice this session; couples calls made within one long-lived harness process | **ABSENT** — sidestepped entirely, not merely bypassed, since the dedicated adapter never imports the module that defines it |
| Retry state | CONTROLLED (zero retries by contract) | **ABSENT** (no retry logic exists in the adapter to control) |
| Global caches (Ollama server-side) | UNKNOWN | UNKNOWN — not independently verified either way this session; flagged, not resolved |
| Environment state (e.g. `OLLAMA_HOST`) | MUST BE ACCOUNTED | MUST BE ACCOUNTED — pin and log explicitly regardless of adapter choice |
| Fallback model selection, hidden automatic retries | MUST BE ACCOUNTED (real, silent, confirmed) | **ABSENT** — no fallback code path exists in a plain HTTP call |
| Model availability (unload/cold-start) | MUST BE ACCOUNTED (a fairness/timing concern, not a correctness one) | MUST BE ACCOUNTED, unchanged |
| Other persistent FeralEcho state | ABSENT | **ABSENT** |

**Recommendation, following directly from this table**: adopt the dedicated adapter (§12), not `_ollama_query()`/`stream_query_ollama()`. This is not merely "cleaner" — it structurally eliminates four of the ten listed channels rather than requiring them to be individually monitored and controlled.

## 14. Generation event schema

One record per real generation call, minimum fields: `arm`, `history_id`, `task_id`, `strategy_id`, `model` (name), `model_config` (the full options dict actually sent — temperature, num_ctx, etc.), `prompt_hash` (sha256 of the exact rendered prompt text), `generation_call_count` (expected always 1 under the zero-retry contract — logged as a verifiable check, not assumed), `retry_count` (expected always 0 — logged as a check), `input_tokens` (`prompt_eval_count`, confirmed available from the real API response), `output_tokens` (`eval_count`, confirmed available), `context_length` (the configured `num_ctx`, since the backend does not independently report what was actually used), `timeout` (bool), `success_failure` (bool, whether any well-formed response was received — distinct from task correctness, which is the evaluator's concern, not the generation ledger's), `elapsed_time` (`wall_s`, confirmed available), `fallback_behavior` (expected always `"none"` under the recommended dedicated-adapter design), `seed` (the exact integer sent, confirmed supported), and a fixed `determinism_note` field, using Codex's own precise phrasing directly rather than restating it worse: *"same seed is a requested sampling control, not a guarantee of bit-identical generation across backend states."*

## 15. Matched-cost invariant

**MUST be equalized across every arm, at holdout/final-evaluation time specifically**: number of model calls per decision (exactly one, zero retries), the configured input/output token ceilings, the available strategy menu, tool access (none), the evaluator-call contract per candidate. **MAY be measured and accounted for rather than force-equalized**: actual consumed tokens (naturally varies with content even under identical ceilings — measure, report, never pad), wall-clock (varies with backend load — measure, randomize arm execution order, don't force-equalize), Arm C's prospective-phase acquisition cost (explicitly *not* required to match Arms A/B's zero prospective cost — reported separately, never silently folded into the holdout comparison, matching every prior report's identical conclusion this session). Retrieval operations: not applicable, excluded from this design by construction. This entire section confirms, rather than revises, what the design and trusted-boundary reports already established — worth stating as convergent agreement across four independent passes, not as new work.

## 16. Retry/fallback accounting

**Materially simplified by the §12 recommendation**: a plain `requests.post`-based dedicated adapter has no retry or fallback logic to hide, making "hidden retry/fallback" **ABSENT by construction** rather than merely "disabled by policy." If, contrary to this recommendation, `_ollama_query()`/`stream_query_ollama()` were used instead, every behavior the mission names (silent retry, model switch, temperature change, context change, fallback invocation, failure suppression, differential health checks) would require explicit, separate instrumentation to detect and log — specified here as the *fallback plan's* requirements only, not the primary recommendation.

## 17. Determinism and pairing

**IDENTICAL across paired arms within one history**: the development-frozen `S0`/menu/feature-map; the exogenous task/order sequence (drawn once per history, shared by every arm in that history); model identity/digest (pinned, checked at freeze and again at teardown); the configured generation parameters; resource limits; the cost-accounting rule. **MAY be randomized, but must be prospectively drawn and fully logged, never left ambiguous**: the specific task/world draws per history; arm execution order within a decision cycle (to control for backend-load/warmth drift); the selector's own choice-randomness seed, as a stream separate from generation randomness (per the trusted-boundary report's three-stream requirement, independently re-confirmed as necessary here). **The backend's own generation is explicitly not assumed deterministic even under a fixed seed** — adopting Codex's own precise caution directly — compensated for via paired, replicated histories and reported uncertainty, never via an assumption of exact reproducibility.

## 18. Artifact provenance package

Minimum immutable evidence per history, reusing `freeze.py`'s hash-and-write-once pattern (confirmed reusable across every prior report this session, and directly precedented in AP-0's own `qual.py::verify_freeze()`): frozen task/world definitions (new, research-owned — built using AP-0's own task-generation *ideas*, never touching AP-0's own sealed files); the hidden-evaluator's code hash and version; strategy-menu/prompt-template hashes; the pure selector's code hash and its `S0` checkpoint hash; a unified event-log schema version (see below); candidate output hashes (and, following this session's own earlier candidate-preservation discipline, the full candidate source too, at negligible marginal cost, as write-only audit evidence); restart/restoration evidence (process exit codes, checkpoint-load confirmations); an environment fingerprint (OS, Python, Ollama versions, model digest); the full experiment configuration, in `FREEZE.json`'s own established shape. **"Do not create redundant logs," per the mission's own instruction**: the generation ledger (§14) and the E/U/S/D/O provenance chain (already specified in the trusted-boundary report §10) should be **one unified event log with one consistent schema**, not two separately-maintained systems requiring cross-referencing.

## 19. State persistence and substitution evidence

Restating the five-step chain already specified in the trusted-boundary report (`S1` present → `S0` substituted → effect disappears → `S1` restored → effect reappears identically), with the exact records required to demonstrate it mechanically, without designing the demonstration procedure itself (not authorized here): a checkpoint's full canonical byte representation, not a hash of one field alone — Codex's own correct point that a hash of "the table" doesn't certify the whole boundary, so the manifest must also bind the identities of every *immutable* component (model digest, feature-extractor version, strategy-menu hash) even where those bytes aren't literally re-hashed into the state file; a real process-exit confirmation for the producer process (not merely "a save() call happened," per the mission's own explicit "a save request is not enough" instruction); a load-confirmation log line from the fresh consumer process, distinguishing "loaded from the committed file" from any other path; the full recorded decision trace for both the `S1`-loaded and `S0`-substituted runs, using coupled, matched random assignments so any observed difference is attributable to state, not incidental RNG divergence.

## 20. Failure taxonomy

**TASK FAILURE**: the candidate ran to completion within its resource bounds, produced a well-formed, correctly-typed output, and that output did not match the expected value. This is the only category that ever maps to a real learner-visible FAIL. Timeout, malformed output, and a "ran but wrong" outcome are all ordinary TASK FAILUREs by default, within the declared budget — not administrative exclusions — matching the identical, independently-reached conclusion in both the trusted-boundary report and Codex's own §16.

**INFRASTRUCTURE FAILURE**: established by *trusted launch/controller evidence* — a specific, recognized denial-class exit code from the sandbox mechanism itself, a confirmed evaluator-process crash, a confirmed backend-unavailable condition — **never** by parsing candidate-produced stderr text (Codex's own sharp, independently-verifiable point: a candidate could trivially print a string like `"sandbox_apply"` itself to fake an infra-failure exemption, so text-matching on candidate output must never be the classification mechanism). Sub-cases: GENERATION FAILURE (the backend never produced a candidate at all — genuine infrastructure); EVALUATOR FAILURE (the trusted comparison logic itself raises — genuine infrastructure, and should halt/alert for researcher review, never silently record any task outcome); MODEL UNAVAILABLE and RESOURCE EXHAUSTION — both genuine infrastructure.

**Per the mission's explicit instruction**: infrastructure failures must never silently become FAIL learning feedback unless this specific convention is pre-registered. The default, safer convention specified here: genuine infra failures are excluded from the primary outcome denominator, handled via a prespecified, outcome-blind replacement/block-invalidation rule, with the exclusion *rate itself* reported and checked for balance across arms — matching the trusted-boundary report's own statistical-plan requirement, not a new invention.

## 21. Engineering acceptance tests

Specified conceptually, per the mission's ten named categories, none executed:

1. **Evaluator secrecy**: a battery of deliberately introspective candidate fixtures (bare-name reference attempts reworked for the new architecture, `globals()`/frame-inspection probes, attempts to open known oracle-artifact paths by name under the perfect-information assumption) — every one must fail to obtain any expected value, confirmed by inspecting what the candidate's own bounded output/stdout actually contains, never by trusting a candidate's self-reported success.
2. **Filesystem isolation**: a candidate attempting to open a real, planted decoy "hidden-evaluator artifact" at a path the sandbox is meant to deny must fail with a genuine access-denial error, confirmed via the sandbox's own enforcement evidence.
3. **Cross-case isolation**: a sequential pair of cases where the second candidate's own execution attempts to read anything the first case's execution might have left behind (temp file, env var, side effect) — confirmed to find nothing, via fresh, never-reused, unique scratch roots per case.
4. **Feedback sanitization**: a structural/type-level test confirming the learner's `update()` function's own signature accepts only the three declared fields (§11) — making the presence of any forbidden field (stdout tail, exception text, timing) a type error, not merely a policy violation that could be silently missed.
5. **Generation accounting**: a small synthetic run where every real generation call, including one deliberately forced to time out, appears exactly once in the generation ledger with a complete schema (§14) — confirming the timeout is recorded, not silently dropped.
6. **Cost parity**: a synthetic paired-arm run where call counts and budget ceilings are confirmed exactly equal, and actual token counts are confirmed balanced within a pre-declared tolerance, reported honestly if not met.
7. **State persistence**: the real five-step `S0`/`S1` chain (§19), run end-to-end with genuine process exits (not merely function returns) between each step, confirmed via process-exit-code inspection and a fresh-process load-confirmation log line.
8. **State substitution**: the `S0`-substituted run reproduces Arm B's own decision pattern exactly under matched deterministic inputs, and the `S1`-restored run reproduces the original Arm C decision pattern exactly — any discrepancy fails this test.
9. **Artifact freezing**: every artifact named in §18 is present, and every recorded hash matches a freshly recomputed hash of the actual file — reusing `freeze.py`'s/`qual.py`'s own already-proven `verify_freeze()`-style pattern directly.
10. **Infrastructure classification**: a synthetic run seeding a known real infra failure (e.g., killing the sandbox subprocess mid-run) and confirming the controller correctly classifies it as infrastructure, not task failure, and that this classification is never influenced by anything the (now-dead) candidate process printed before termination.

## 22. Minimal implementation surface

Adopting and lightly extending Codex's own §23 table structure, reformatted to the mission's exact requested fields, with one independently-added revision (item 2's cost is materially lower than Codex's own framing implies, per §12's new finding):

| # | File/component | Purpose | New/modified | Prod/research-only | Invariant protected | Acceptance test | Rollback |
|---|---|---|---|---|---|---|---|
| 0 | `research/rung1/protocol.json`-style manifest | Freeze the information/state/cost/arm/replay contract before any code | New | Research-only | No essential convention withheld; no ambiguous outcome/cost/replay rule | Static completeness review | Supersede draft; preserve prior evidence |
| 1 | New evaluator/candidate-runner/sandbox-profile package (e.g. `app/experiments/rung1/evaluator.py` + a new `.sb` profile) | §4-§9 trusted boundary | New | Research-only; does not edit `oracle_runner.py`, `safe_exec_wrapper.py`, or any production sandbox | §21 tests 1-4, 7-10 must pass | Full hostile-fixture battery (§21) | Disable/discard the isolated package version; scratch root only |
| 2 | Adopt + extend `app/experiments/accumulation_probe/ollama_client.py`'s pattern into a new `app/experiments/rung1/client.py` | §10-§16 generation contract | **Adopt-and-extend, not new-from-scratch** — meaningfully lower cost than Codex's own framing, per §12's finding | Research-only, zero production imports (confirmed already true of the source pattern) | §21 test 5-6 | Mock-server request/response + failure tests; source/import-side-effect checks | Disable research client; no production wiring exists to undo |
| 3 | Research task adapter/partition manifest | Frozen public task packet + convention + hidden cases | New (reusing AP-0's task-generation ideas, not its sealed files) | Research-only | No task-information gap between arms; literal partition disjointness | Reference agreement, overlap checks | Discard unused freeze; never reuse exposed material |
| 4 | Pure selector + state serializer + controller-owned event ledger | §11, §18, §19 | New | Research-only | Only validated outcomes update state; E/U/S/D/O mechanically bound | Hand-checkable fixtures, exact-reconstruction tests | Delete/disable isolated state namespace; retain audit copies |
| 5 | History/restart/intervention controller | §19, restart/substitution mechanics | New | Research-only | Real process boundaries; no ambient reads | Mock generations, crash-before-commit, replay-equivalence tests | Stop and archive; no live Echo restart involved |
| 6 | Frozen baseline/development selection + metering | Champion competition (Stage 5, out of scope here except to note it depends on 1-5) | New | Research-only | Credible development-only selection | Lineage-separated validation | Retire candidate set/version; never counted as confirmation |
| 7 | Independent history analysis + final freeze | Stage 5/7, out of scope here | New | Research-only | Correct denominators, joint criterion | Synthetic correlated-history fixtures | Supersede pre-confirmation versions only |

**Strongly prefer new isolated research apparatus over production changes, per the mission's own instruction — satisfied throughout: nothing above modifies production Echo, RiverBrain, AP-0, or any existing sandbox profile.**

## 23. Stage ordering

Derived independently, not copied from either the mission's suggested labels or Codex's own implicit table ordering, though the two substantially agree:

- **Stage 1 — Evaluator boundary** (§22 item 1): build and hostile-fixture-qualify the trusted evaluator/candidate-runner/sandbox profile (§21 tests 1-4, 7, 10). **Blocks everything downstream** — nothing else matters if candidates can read answers.
- **Stage 2 — Generation accounting** (§22 item 2): adopt/extend the AP-0-pattern adapter; define and log the generation-event schema (§14); qualify retry/fallback absence and cost-parity accounting (§21 tests 5-6). **Can proceed in parallel with Stage 1** — the two are independent components — but both must complete before Stage 3.
- **Stage 3 — Task/state substrate** (§22 item 3, plus the selector/feature-map design work named but not specified in §3): freeze the research task packet (full convention included, per Codex's §3 resolution), the two-strategy menu, and the feature-signature granularity. Requires Stage 1 (to know the evaluator's expected output shape).
- **Stage 4 — Provenance/ledger + restart controller** (§22 items 4-5): the unified E/U/S/D/O event log and the multi-process restart/substitution controller (§21 tests 8-9). Requires Stages 1-3.
- **Stage 5 — Baseline/champion development + pilot** (§22 item 6): the champion-selection competition and a small development-only pilot for variance/effect-size estimation. Requires Stages 1-4 fully qualified — a pilot run through an unqualified evaluator would be meaningless.
- **Stage 6 — Adversarial preflight against the fully assembled apparatus**: component-level qualification does not guarantee the *assembled* system has no emergent gap (e.g., a timing side-channel that appears only when the real controller and real sandbox interact under real load). A dedicated final pass is required, not assumed satisfied by Stages 1-5's individual tests.
- **Stage 7 — Confirmatory histories**: only after Stage 6 passes, and only with a separate, explicit authorization this document does not grant.

## 24. Stop conditions

Concrete and falsifiable, each tied to a specific test above: candidate can still access expected outputs (§21 test 1 fails) → stop before Stage 1 completes. Hidden evaluator data reaches the learner (§21 test 4 fails, or any forbidden field is structurally reachable) → stop. Generation retries are unobservable (the ledger under-counts real backend calls, per a synthetic forced-retry fixture) → stop before Stage 2 completes. Model fallback differs across arms (`fallback_behavior` is ever non-`"none"` under the dedicated adapter, or an undeclared fallback is used and not uniformly logged) → stop. Complete selector state cannot be checkpointed (a save/restore round-trip fails to reproduce identical decisions under matched inputs) → stop before Stage 4 completes. Cost parity cannot be measured (any arm's ledger token/call fields are missing or unreliable) → stop before Stage 2/5. Infrastructure failures contaminate learner feedback (any FAIL bit traced back to a confirmed infra event) → stop immediately at any stage and treat as a design defect requiring a fix before any further data collection, not a statistical footnote.

## 25. Remaining unknowns

Whether macOS Seatbelt exposes parent/sibling-process enumeration to a denied-by-default child (§7) — not independently tested. Whether the shared `(allow mach-lookup)` allowance, already accepted as unavoidable in the production F2 sandbox for ObjC/CoreFoundation runtime internals, could be exploited as a covert channel in this narrower research context — not independently tested. Whether the Ollama server performs any request-level caching relevant to reproducibility — not verified. The real routing-opportunity headroom of the eventual two-strategy menu on the chosen task packet — an empirical, Stage-5 development question, correctly out of scope here. The real per-history variance needed for final sample-size justification — a Stage-5 pilot question, unresolvable on paper.

## 26. Engineering-gate verdict

**SPECIFICATION-READY.** Every genuinely blocking invariant for the two named engineering gates (trusted evaluator isolation, generation accounting) now has a complete, specific, buildable specification in this document — extending, not merely restating, Codex's own gate. This is explicitly **not** READY-FOR-APPARATUS: nothing described here has been built, and per the mission's own instruction, an unimplemented specification must never be called ready apparatus, regardless of how complete the specification is.

## 27. Final recommendation

Authorize, as a **separate, future, explicit decision** — not by this report — exactly Stage 1 and Stage 2 as the first buildable increment: the trusted evaluator boundary and the generation-accounting adapter. These two are independently specified, independently testable via the acceptance battery above, and block literally everything else regardless of how later development/pilot work turns out. This matches both Codex's own final recommendation and the mission's own closing framing.

---

**TRUSTED EVALUATOR INVARIANT:** DEFINED

**EXPECTED-ANSWER ISOLATION DESIGN:** CONDITIONAL

**CANDIDATE OUTPUT CONTRACT:** CONDITIONAL

**LEARNER FEEDBACK CONTRACT:** QUALIFIED

**GENERATION PATH:** CONDITIONAL

**GENERATION ACCOUNTING:** CONDITIONAL

**MATCHED-COST INVARIANT:** DEFINED

**RETRY/FALLBACK VISIBILITY:** PARTIAL

**STATE PERSISTENCE EVIDENCE:** CONDITIONAL

**ENGINEERING ACCEPTANCE TESTS:** COMPLETE

**MINIMAL IMPLEMENTATION SURFACE:** DEFINED

**PROJECT STATE:** SPECIFICATION-READY

**IMPLEMENTATION AUTHORIZATION:** NO

**1. What exact engineering flaw currently prevents the Rung-1 experiment from being trustworthy?** `oracle_runner.grade()` executes candidate code and the hidden expected-value table (`_CASES`) in the same Python module and namespace, so a candidate can read the answer directly by name; separately, neither existing generation helper offers a genuinely isolated, seeded, fully-metered, no-implicit-fallback request contract.

**2. What is the smallest repair that closes it?** Replace whole-suite, same-module execution with per-case, process-separated execution — a trusted controller holds expected values and performs the comparison after a sandboxed child (receiving only the permitted input) returns only a typed, size-bounded output — reusing the existing sandbox-exec mechanism, restructured; combined with adopting AP-0's existing `ollama_client.py` pattern, which already supplies most of the needed seed/metering/no-fallback contract.

**3. How will we prove candidate code cannot obtain expected answers even while knowing the evaluator design?** A hostile-fixture acceptance battery (§21, items 1-4) run against the actual assembled boundary, checking every named channel (globals, frames, files, environment, descriptors, process enumeration, IPC, timing, serialization tricks) by inspecting the sandbox's own enforcement evidence, never the candidate's self-report.

**4. How will we prove adaptive and control arms receive comparable test-time generation resources?** A unified generation ledger recording every real call's model/config/tokens/timing/retry-count/fallback-status for every decision in every arm, checked post hoc for exact equality on dimensions that must be equalized and for balance within a pre-declared tolerance on dimensions that naturally vary.

**5. What exact acceptance tests must pass before prospective trials are allowed?** The ten categories in §21, plus a final adversarial preflight against the fully assembled apparatus (Stage 6) — not merely its individually-qualified components.

**6. Does any remaining blocker require more learning theory, or are the remaining problems purely engineering?** Purely engineering, independently confirmed rather than merely accepted — every remaining item is a concrete, buildable, testable specification; none requires resolving what Rung 1 means or redesigning the claim.

**7. What is the smallest implementation mission you would authorize NEXT, assuming this specification survives adversarial review?** Stage 1 and Stage 2 together, as one bounded, research-only, independently-qualifiable increment — the trusted evaluator boundary and the generation-accounting adapter, and nothing else: not the selector, not the task packet, not the champion, not any prospective trial.
