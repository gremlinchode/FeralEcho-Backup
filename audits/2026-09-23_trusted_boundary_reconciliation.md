# Trusted-Boundary Reconciliation: Codex's Pre-Mortem Against the Preregistered Routing Design

Read-only. Git HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce` unchanged before and after (confirmed by direct `git rev-parse` before and after this investigation). No production, RiverBrain, AP-0, prompt, routing, evaluator, task generator, or persistent-state file was touched. No prospective trial was run, no model call was made.

**Source under attack**: `audits/2026-09-22_persistent_learning_experiment_premortem.md` (Codex), reviewed against `audits/2026-09-22_preregistered_persistent_routing_experiment_design.md` (mine, the design it attacks) and against fresh, independent source reads performed in this session — not against Codex's prose alone. Where I could independently reproduce a claim from source, it is marked **OBSERVED** in my own voice, not merely relayed. Where I could not reproduce or check something in the time available, it is marked **UNKNOWN**, not inherited as fact.

**I am not defending my prior work.** The single most important finding in this document is that my own prior evaluator-qualification report's central recommendation — reuse `oracle_runner.grade()` unmodified — is wrong, and my prior design's `TASK CORRECTNESS: QUALIFIED` verdict must be withdrawn. I independently reproduced the mechanism from source before accepting Codex's claim, and it holds.

## 1. Executive verdict

**Codex's central claim is CONFIRMED, independently, from source alone, with no execution required.** `app/experiments/accumulation_probe/tasks.py`'s `make_test_code()` writes `_CASES = <literal list of (args, expected) pairs>` as a bare module-level global into the same script `oracle_runner.grade()` concatenates with candidate code and runs as one Python module. A candidate function, once invoked from that module's own test loop, executes inside that same global namespace — it can reference the bare name `_CASES` directly (ordinary Python name resolution, no reflection trick required) and return the pre-computed expected value for its own arguments, scoring a full, legitimate-looking PASS while solving nothing. Neither the nonce (which only prevents pre-computing the pass-marker string in advance) nor `jail.py`'s filesystem confinement (which governs paths, not intra-process namespace visibility) do anything to prevent this. **This is fatal to my prior claim that "hidden task correctness is AVAILABLE" as currently specified**, though not fatal to the underlying research question — a repaired evaluator boundary is specifiable using the same underlying sandbox mechanism, restructured rather than replaced.

Beyond the evaluator, Codex found one genuine internal self-contradiction in my own design (the replay-from-checkpoint section simultaneously claims a fixed-trace replay and a diverging-trajectory rollout, which cannot both be true — confirmed by re-reading my own §11 verbatim), one real, previously-unaddressed structural gap (nothing in my design specified the feature-signature's granularity, and if it is too fine, the T→S transfer claim is impossible by construction, not merely hard to demonstrate), two real corrections to my interpretation matrix (NEAR success is the *good* outcome, not overgeneralization; UNREL improvement is ambiguous, not automatically a confound), and a resolution to my own prior UNKNOWN about `_ollama_query()`'s circuit breaker (real, in-memory, process-scoped, traceable to `echo_model_orchestrator.py`, and controllable). Every one of these is independently reproducible from source, and every one of them is repairable without abandoning the experiment's core architecture (standalone selector, fixed strategy menu, AP-0 substrate, three arms, lineage-as-unit). **Verdict: B — repairable with small, specified changes** — with the explicit caveat that "small" does not mean trivial for the evaluator-boundary repair specifically, which is real, if bounded, new engineering.

## 2. Codex attack reconstruction

Codex's report is complete (20 sections, a closing integrity check, hash fingerprints, and a final judgment block — not truncated by a token-budget exhaustion, per its own §18-20 and closing fingerprint table). Objections, classified by the mission's own four buckets, using Codex's own OBSERVED/INFERRED/PROPOSED/UNKNOWN labels as a starting point but re-verified rather than trusted:

| Objection | Codex's own label | My independent finding |
|---|---|---|
| Same-module candidate/expected-answer access | OBSERVED | **OBSERVED, independently reproduced — fatal to the current evaluator, repairable (§3/§4)** |
| `jail.py` docstring overstates its actual scope | OBSERVED | **OBSERVED, independently reproduced (§5) — real but narrow; overstating it was my own error** |
| Evaluator stdout/stderr/tails leak expected-value fragments | OBSERVED (re-confirms my own prior finding) | **OBSERVED — I found the same tail-truncation risk in my own 2026-09-22 evaluator report; Codex adds that the test loop *deliberately* prints failing input/actual/expected, a stronger, by-design leak, not an incidental one** |
| Replay-from-checkpoint's two paragraphs contradict each other | OBSERVED | **OBSERVED, independently reproduced by re-reading my own §11 — a genuine, unambiguous internal contradiction, not a matter of interpretation** |
| `_ollama_query()` circuit breaker is real, in-memory, traceable | OBSERVED | **OBSERVED, independently traced to `echo_model_orchestrator.py:1254-1283` this session — resolves my own prior UNKNOWN** |
| `_ollama_query()` has no seed parameter, returns no telemetry, has a silent fallback path with different controls | OBSERVED | **OBSERVED, confirmed by re-reading the function's own signature/docstring this session** |
| AP-0 partition disjointness is not literally guaranteed, only seed-labeled | INFERRED (constructed counterexample) | **Plausible and unrefuted — I did not independently regenerate the palindrome/category_of pools to confirm the exact collision, but the generator's own support size (7 fixed palindrome strings, 6 status codes) versus the default 10-case request makes the pigeonhole argument sound on its face; treated as a real, live risk, not dismissed** |
| Experimental unit is the lineage/history, not the task | INFERRED | **CONFIRMED as already correct in my own prior design (§3 of my design already named the lineage as the unit) — Codex's contribution here is real *additional* precision (task-order-within-lineage as a further correlation source), not a correction of an error** |
| NEAR success should read as correct instruction-following, not overgeneralization; UNREL improvement is ambiguous, not automatically a confound | INFERRED | **CONFIRMED as a real error in my own interpretation matrix (§8 below) — I misread AP-0's own NEAR construction** |
| Feature-signature granularity was never specified, and if too fine, S-transfer is impossible by construction | INFERRED | **CONFIRMED as a real, previously-unaddressed gap in my own design (§8 below)** |
| No competent frozen-champion selection *procedure* was specified, only "hand-built" | INFERRED/PROPOSED | **CONFIRMED — my design under-specified Arm A; Codex's development/validation-split selection procedure is a genuine improvement, not merely an alternative** |
| Statistical plan needs multi-history replication, an explicit joint-success rule, and timeout handling matching the real grader's own distinct classes | PROPOSED, building on OBSERVED gaps in my design | **CONFIRMED — my design's exclusion-of-timeouts language does not match `grade()`'s own real `infra`/`timeout` distinction, which I had not checked against my own exclusion rule** |
| AP-0 qualification (the live, in-progress gate run) is itself incomplete, per real result files | OBSERVED, citing specific JSON artifacts | **Not independently re-verified in this pass (time-boxed) — treated as UNKNOWN pending a direct re-read of the cited summary files, but not load-bearing for this document's own verdicts, since my design never depended on AP-0's *current* qualification run succeeding** |

No objection in Codex's report needed to be strengthened on its behalf to be taken seriously — the ones I could independently check all held as stated or close to it. The one place I judge Codex's own language slightly overreaches is calling the entire jail "not enforcing its docstring's claim" — true for filesystem reads outside the experiment root, but the *within-experiment-tree* confinement genuinely does work as documented, which matters for scoping the repair (§5).

## 3. Candidate/expected-answer address-space audit

Traced directly from source, not from Codex's citation alone — every claim below was independently re-derived by reading the actual files this session.

- **Where is candidate source loaded?** `oracle_runner.grade(candidate_code, test_code)` (`app/experiments/accumulation_probe/oracle_runner.py:41-48`) builds `source = candidate_code + "\n\n" + test_code.replace("@@NONCE@@", nonce)` and passes it to `run_script()`, which writes this single combined string to one temp file (`_script.py`) and executes it as a plain script via `sandbox-exec -f echo_sandbox.sb ... safe_exec_wrapper.py <scratch> <path> --mode=script`.
- **Where are hidden cases loaded?** `app/experiments/accumulation_probe/tasks.py`'s `make_test_code(fn, cases)` (confirmed by direct read, line 246) returns exactly: `f"\n_CASES = {lit}\n" + f"def _ap0_run():\n    for a, e in _CASES:\n        try:\n            r = {fn}(*a)\n        except Exception as ex: ...\n"` — `_CASES` is a bare, module-level assignment, `lit` is the literal repr of the real `(args, expected)` pairs.
- **Where do expected values exist?** Inside `_CASES`, in the same file, same namespace, as the candidate's own function definitions.
- **What globals are visible to candidate code?** The candidate's function object, once `exec()`'d as part of this one script, has `__globals__` equal to the script's own module dict — which contains `_CASES`, `_ap0_run`, and everything else defined earlier in the file, including the candidate's own other top-level definitions. This is ordinary CPython semantics for a single-module script; no special access or introspection library is required.
- **What imports can candidate code perform?** Whatever the sandbox profile allows — confirmed (§5 detail) that `echo_sandbox.sb` (the profile `oracle_runner.py` actually uses for grading, distinct from AP-0's own `jail.py` used for *generation*) contains `(allow file-read*)` unconditionally — real, unrestricted read access to any file the OS-level user can read, network denied unconditionally, writes confined to `SCRATCH`.
- **Can candidate code introspect its module / inspect globals / inspect frames?** Yes to all three, trivially: a bare reference to `_CASES` inside the candidate function's own body is sufficient (no `globals()` or `sys._getframe()` needed, though both would also work and would be even less detectable). This requires no special privilege — it is exactly how Python closures/module-level code already work.
- **Can it recover `_CASES` or equivalent hidden state?** Yes, directly, by name.
- **Can it access expected values indirectly?** Yes — in addition to the direct global reference, the unrestricted `(allow file-read*)` sandbox policy means the candidate could also simply `open()` and read its own concatenated source file from disk (the temp file `run_script()` wrote) to recover the identical text, a second, independent route to the same information.
- **Does the nonce-gated success marker prevent this?** No — the nonce (`secrets.token_hex(8)`, generated after generation, substituted into the pass-marker string) prevents a candidate from *pre-computing* the literal marker text in advance of its own generation. It does nothing about a candidate that, once running, computes a *correct-looking output* via table lookup rather than real logic — the real test loop still legitimately observes matching values and legitimately prints the real (nonced) marker, because the *comparison itself*, not just the marker, has been defeated.
- **Does sandboxing prevent it?** No — Seatbelt/`sandbox-exec` governs filesystem writes, network, and (in `echo_sandbox.sb`'s case) process-fork/spawn at the kernel syscall layer; it has no mechanism for, and was never designed to restrict, which Python-level global names a function defined in the same process can read. This is a language/architecture-level gap, categorically outside what an OS-level sandbox addresses.

**Minimal conceptual proof-of-concept, described, never executed, per the mission's explicit instruction**: a candidate whose body is, in essence, `for a, e in _CASES:\n    if a == args_tuple:\n        return e` (with some benign-looking wrapper around it) would pass every visible test case with zero real problem-solving logic. No malicious or destructive code was written or run to confirm this; the claim is fully established by reading `make_test_code()`'s own returned string structure and `grade()`'s own concatenation order, which is sufficient and was the mission's own stated bar ("do not reason from documentation alone... trace the actual runtime boundary" — satisfied by tracing the literal generated source, not by running it).

**Answer to the mission's core question: YES.** Task correctness, as currently specified, is not yet independently established — a candidate can obtain enough trusted evaluator state (the entire `_CASES` table, verbatim, via ordinary name resolution) to produce the expected answer without solving the intended task.

## 4. Evaluator trust-boundary audit — defining the correct boundary

The mission's own conceptual structure is the right target; the question is whether it requires new infrastructure or a restructuring of existing infrastructure. **It requires restructuring, not new infrastructure — the underlying sandboxed-execution mechanism (`sandbox-exec` + `echo_sandbox.sb`/`safe_exec_wrapper.py`) is reusable; the *call shape* around it must change.**

Minimum sufficient design:

- **UNTRUSTED**: candidate code, containing only its own function definition(s), is `exec()`'d **alone**, in its own fresh, minimal namespace — never concatenated with `_CASES` or any test-authoring code in the same source file passed to the interpreter.
- **TRUST BOUNDARY, enforced by process separation, not merely namespace separation**: a genuinely adversarial candidate can still, within one OS process, use frame introspection (`sys._getframe()` walking up the call stack) to inspect a *caller's* local variables even across separate Python namespaces in the same interpreter — namespace separation alone is insufficient against a maximally adversarial candidate; only OS-level process separation reliably closes this. Concretely: the candidate is invoked in its own sandboxed subprocess (reusing `oracle_runner.run_script()`'s existing `sandbox-exec` invocation, per-input-case rather than per-whole-suite), receives one input via argv/stdin, computes and prints one output, and exits.
- **TRUSTED**: a separate process (the harness controller, never itself running inside the candidate's sandbox) holds `_CASES`/expected values in its own memory, was never on the candidate's own filesystem-readable path, and performs the comparison between the candidate subprocess's returned output and the expected value **after** the candidate subprocess has already run and exited.
- **TRUSTED**: rich evaluator evidence (full stdout/stderr, timing, per-case detail) stays in a researcher-only audit channel, written by the trusted controller, never by anything the candidate process could write to or that the learner reads.
- **SANITIZATION BOUNDARY / LEARNER**: exactly as my prior design already specified (§6/§10 there) — PASS/FAIL only, extracted by the trusted controller from its own comparison, never from anything the candidate process emitted beyond its raw computed output.

**This reuses `oracle_runner.py`'s existing sandbox-exec mechanism**, restructured from "one subprocess call graded against a concatenated test suite" to "one subprocess call per test case, receiving only the input, returning only the output, graded by the trusted controller outside the sandbox." The cost is real (more subprocess spawns per candidate) but modest, and it is a specification change to an existing mechanism, not an invention. **Not implemented or verified here — this is the specified repair, not evidence that it has been built.**

## 5. `jail.py` audit — honest reinspection

Re-read the exact profile string directly this session (`app/experiments/accumulation_probe/jail.py:6-10`):

```
(version 1)(allow default)(deny file-write*)
(allow file-write* (subpath "{arm}") (literal "/dev/null") (literal "/dev/dtracehelper"))
(deny file-read* (subpath "{exp}"))(allow file-read* (subpath "{arm}"))
```

**What this actually establishes, precisely**: `(allow default)` is the global starting posture — nearly everything is permitted unless a later `deny` clause narrows it. The two `deny`/`allow` pairs that follow narrow exactly two things: (1) writes are denied everywhere *except* inside the arm's own subdirectory, and (2) reads are denied inside the *experiment root* (`{exp}`, e.g. `memory/experiments/accumulation_probe/...`) *except* inside the arm's own subdirectory (which is nested inside `{exp}`). **Everything outside `{exp}` — the live repository's own source code, `.git` history, any other file the invoking user can read — remains fully readable**, because nothing denies reads there; only the experiment tree itself is scoped down. There is **no network-deny clause anywhere in this profile** — `(allow default)`'s permissive posture for networking is never subsequently narrowed, so outbound network access beyond the intended Ollama endpoint is not restricted. There is **no process-execution/fork restriction** (unlike `echo_sandbox.sb`, whose own header comment explicitly documents denying fork/process-spawn — `jail.py` has no equivalent clause). `run_jailed()` (`jail.py:12-15`) passes `env = {**os.environ, **(extra_env or {})}` — the full parent process environment, unfiltered, is inherited by the jailed subprocess. No inherited-file-descriptor handling is present (unlike `safe_exec_wrapper.py`'s own documented fd-0-closing discipline for the production F2 path).

**Strongest legitimate claim about `jail.py`, stated precisely**: it establishes write confinement (an arm can only write inside its own subdirectory) and **read confinement specifically within the AP-0 experiment artifact tree** (an arm cannot open the oracle/other-arms'/frozen-worlds files sitting elsewhere under `memory/experiments/accumulation_probe/...`) — a real, working, narrow safeguard against one specific attack (a candidate directly path-opening a sibling arm's or the oracle's files). **It does not establish general filesystem confinement, network confinement, process-execution confinement, or environment-variable confinement**, and my own prior evaluator-qualification report's characterization of it as "OS-level isolation" without this qualification was an overstatement I retract here. This does not affect §3/§4's finding (the same-module answer-access flaw is a namespace problem, not a filesystem-confinement problem, so `jail.py`'s real or claimed scope is orthogonal to it) — but it is a real, separate gap that any rescued experiment's own generation-arm confinement would need to close (broaden the read-deny to the whole filesystem outside an explicit allowlist, add an explicit network deny scoped to the Ollama endpoint only, restrict environment variables to a minimal allowlist, and add process-execution restrictions matching `echo_sandbox.sb`'s own precedent) before being trusted for a real experimental run.

## 6. Feedback information-flow audit

Every field `oracle_runner.grade()` can return, classified:

| Field | Classification | Reasoning |
|---|---|---|
| `passed` (bool) | **SAFE FOR LEARNER** | The minimal, sufficient signal — once the evaluator boundary (§4) makes this trustworthy |
| `ran_ok` | **CONDITIONAL** | Distinguishes "ran but failed" from "crashed" — arguably useful bookkeeping, but reveals more than one bit; declined by default, same reasoning as coarse failure-class in my prior design |
| `output_tail` (300 chars of stdout) | **MUST NOT REACH LEARNER** | Confirmed, independently, that `make_test_code()`'s own generated loop *deliberately* prints the failing `(args, actual, expected)` tuple on a mismatch — this is a by-design leak of the exact expected value, not an incidental `AssertionError` side effect |
| `error_tail` (300 chars of stderr) | **MUST NOT REACH LEARNER** | Can contain exception values, tracebacks, source lines, paths |
| `infra` / `timeout` (bool) | **RESEARCHER ONLY** | Real, useful administrative classification (my prior design already used this correctly for exclusion accounting) — but must never reach the learner's own update signal |
| `duration` | **MUST NOT REACH LEARNER** | Codex's timing side-channel point is real: differential timing across failing cases can leak which case failed, a subtle but genuine encoding of expected-value structure |
| Case counts / cases reached | **MUST NOT REACH LEARNER** | Reveals partial-credit structure not present in a pure PASS/FAIL signal |
| Task/world/seed metadata, filenames | **MUST NOT REACH LEARNER** | A direct route to task-ID/split recognition — would let a selector key on internal bookkeeping instead of task-time features, corrupting the specificity design (§8) |
| Full raw `grade()` dict, for offline human review | **RESEARCHER ONLY** | A separate, append-only audit log the harness's own decision logic never reads |

**Minimum learner-visible feedback contract, confirmed unchanged from my prior design and now independently validated by Codex's own §5 arriving at the identical conclusion**: exactly one PASS/FAIL bit, bound to an episode identifier, delivered only after the episode is irrevocably complete. **The one real change required**: this bit must now be sourced from the *repaired* trust-boundary comparison (§4), not from `grade()`'s current single-process dict — the current dict's `passed` field cannot be trusted as ground truth until the evaluator itself is rebuilt, since a same-process candidate could have already defeated the comparison that produced it.

## 7. Revised task-correctness verdict

**My prior verdict, `TASK CORRECTNESS: QUALIFIED`, is withdrawn.** The mission's own three-way distinction, answered honestly and separately:

- **Correctness machinery exists?** Yes — `oracle_runner.grade()`, `make_cases2()`'s mutant-killing case construction, and the underlying sandbox-exec mechanism are all real, functioning code, independently confirmed.
- **Correctness machinery is secure against answer access?** **No** — §3 establishes this directly and concretely, not speculatively.
- **Correctness machinery is ready for this experiment?** **No**, not without the restructuring specified in §4, which is designed but not built or verified.

**Revised verdict: NOT QUALIFIED, as currently specified and unmodified.** With the §4 repair specified (but not yet built or independently verified), the honest forward-looking status is **CONDITIONAL** — repairable, not disqualifying, but not usable today.

## 8. AP-0 transfer interpretation

**The signature-table objection, tested on its own logic, holds.** A persistent table of `(task/context signature) → per-strategy outcome statistics` — with no mechanism to propose a new strategy and no mechanism to change its own feature representation — can, in principle, improve measured performance across every one of AP-0's T/S/NEAR/UNREL splits without acquiring any reusable abstraction, exactly as Codex constructs. **This does not invalidate the splits; it bounds what they establish**, and my prior design's own bounded claim (§2 there: "improved *strategy selection*," never "improved abstraction") was already correctly scoped at the top level — but two concrete errors in how I applied that scoping must be corrected:

1. **NEAR is misread in my prior interpretation matrix.** AP-0's own `worlds.py::mismatch()` (independently re-read this session) constructs NEAR tasks with an **explicitly stated, conflicting convention** — a NEAR task tells the solver the rule is different this time. A selector that correctly applies the *stated override* on NEAR is demonstrating appropriate, feature-conditioned behavior, not overgeneralization — **NEAR success is the good outcome, and NEAR failure (blindly reapplying the T/S-learned convention despite an explicit override) is the concerning one.** My prior table had this backwards. Corrected.
2. **UNREL improvement is not automatically a confound.** A genuine, benign improvement in general response quality (better formatting, fewer careless errors) could raise UNREL performance without indicating anything wrong — Codex is right that this needs a stated precision/equivalence criterion to interpret a "flat" or "improved" UNREL result, not an automatic verdict either way. My prior blanket "any UNREL improvement is a red flag" is too strong. Corrected: UNREL requires investigation on any nontrivial deviation, not an automatic negative label.
3. **A previously unaddressed, structural gap**: my prior design never specified the feature-signature's granularity. If the selector's signature key is, e.g., the exact function name (a natural, naive default), and S-split function names are by design never seen during the prospective phase's T-only accumulation, then the S-key's table entry never updates at all — it stays at its development-phase default, meaning the adaptive arm's behavior on S is **structurally identical to the frozen twin's**, regardless of how well the update mechanism works, unless the signature is deliberately coarsened to a shared representation (e.g., "K1, ranking-style task, dict-shaped input" vs. "K1, ranking-style task, string-shaped input" sharing a coarser "K1-ranking" bucket). **This must be a deliberate, pre-registered design choice, frozen before any run** — left implicit, the T→S transfer claim is not merely hard to demonstrate, it is impossible to demonstrate by construction, in the direction that would make a positive result unfakeable but also unreachable.

**Correctly bounded, per split**: **T** (fresh instances of the same template/kind seen during prospective accumulation) establishes repetition-level routing benefit only. **S** establishes narrow structural-variation transfer, *conditional on* the signature-granularity choice above being made deliberately and frozen in advance. **NEAR** tests specificity/correct instruction-following under an explicit override — success is positive evidence of feature-conditioned (not blanket) routing. **UNREL** is a genuinely weak, ambiguous control needing its own stated equivalence criterion, not an automatic verdict.

**A prospectively withheld rule family** (a wholly new convention kind, never seen in any phase, not even development) would be a stronger test of abstraction specifically, since success there could not be explained by any finite table keyed on K1/K2/K3-specific signatures — correctly named by Codex as a separate, later, not-yet-designed experiment. Not designed further here, per the mission's own instruction.

## 9. Operational bounded-learning definition

**Yes, a system with frozen foundation-model weights, a fixed update algorithm, a finite strategy menu, persistent experience-dependent statistics, causal state changes, post-boundary behavioral changes, and independently measured improvement can legitimately establish bounded system-level learning.** The operational reason: "learning," at the system level and independent of substrate, is properly defined as *retained state causally changed by evaluated experience, in a way that improves later independently measured performance* — this is the same operational content reinforcement-learning theory already uses for a policy that updates from reward and demonstrably performs better afterward. It does not require weight updates, general applicability, or novel-procedure acquisition to be a real instance of learning; it requires the causal chain (E→U→S→D→O, per my prior design's §10, now needing the §4 repair) to be genuinely established, not merely plausible.

**What it would still not establish, stated exactly**, per the mission's own list: new procedure acquisition (no — the strategy menu is closed and fixed for the life of the experiment); abstraction construction (no, per §8, unless the coarse-signature design choice is deliberately built *and* independently shown to generalize — and even then this is "generalization within a fixed representation," not literal abstraction formation); model-weight learning (no — weights are frozen throughout, by design); general learning (no — scoped to one fixed task family and strategy menu); learning-to-learn/meta-learning (no — the update algorithm itself never changes); open-ended competence growth (no — both the feature space and the action menu are closed); recursive self-improvement (no — nothing here modifies the mechanism doing the learning).

## 10. Reassess the experimental unit

**Codex's argument holds, and it confirms rather than overturns my prior design.** My design's own §3 already named the replicate lineage, not the individual holdout task, as the correct independent unit, precisely because every holdout decision within one lineage shares the same persisted state and is therefore correlated. **What Codex adds is real, additional precision I had not specified**: within the prospective (experience-accumulation) phase itself, task *order* is a further, uncontrolled source of correlation — an early lucky success can lock in a strategy for the rest of the lineage; a late block of easier tasks creates an illusory rising curve with no real improvement. This is not a correction of an error in my design, it is a genuine gap my design left open. **Required addition**: prospective-phase task order must be randomized and pre-registered per lineage, and matched (identical order) between a lineage's paired Arm B/C twins so a lucky ordering cannot asymmetrically favor one arm. The number of independent lineages remains, as my prior design already stated, a pilot-informed decision made before the confirmatory phase, not a convenient number chosen after seeing an early positive result — Codex's insistence on this point matches, rather than contradicts, what I already wrote.

## 11. Replay/counterfactual analysis

**Codex found a real, unambiguous internal contradiction in my own §11, confirmed by re-reading it verbatim.** I wrote that the TRUE and SHAM-REVERSED lineages "replay the identical recorded `(task, strategy_selected, candidate, outcome)` trace" and, in the same section, that they "will genuinely diverge in which task-strategy pairs occur... from the first substituted update onward." These cannot both be true: a trace that is genuinely *replayed identically* fixes, by definition, exactly which task-strategy pairs occur at every step; a design that *lets divergent state drive new selections* is not replaying a fixed trace at all. I conflated two different, both individually legitimate, experimental designs. Resolving this requires picking one, explicitly, not blending their language:

- **Estimand A — fixed-trace update-content sensitivity (adopted here as the primary, minimal intervention).** The real prospective phase is run exactly once, producing one real, recorded `(task, strategy_selected, real_candidate_code, real_oracle_outcome)` sequence. Both TRUE and SHAM-REVERSED replay this **exact** sequence — `strategy_selected` is taken verbatim from the recording at every step, never re-derived from the (deliberately diverging) selector state — and only the *label* fed to `update()` differs (real outcome vs. flipped). This tests, precisely: does the *content* of the outcome label, holding the entire experience sequence fixed, change the resulting persisted state in a way that matters? No new generation, no new oracle call, no RNG state needed for action selection (there is none to make — the sequence is fixed) — genuinely cheap, genuinely a pure replay, and genuinely well-defined. **What it explicitly does not test**: what would have happened if the diverging state had been allowed to make different selections along the way.
- **Estimand B — full online counterfactual rollout (explicitly declined here as out of scope).** Requires real, new generation and real, new oracle calls for whatever different action a diverging policy actually selects at each post-divergence step — there is no way to know the real-world outcome of an action that was never actually taken in the recorded trace without generating and grading it for real. This is a materially larger, genuinely online experimental design with its own new sampling-noise confounds, not a cheap replay, and is not authorized or designed further here.

**On "could label substitution create an impossible counterfactual" (e.g., a PASS label attached to an artifact that actually failed)**: yes, and this is intentional under Estimand A, not a flaw to fix. SHAM-REVERSED deliberately attaches a wrong label to a real artifact's real outcome. This is explicitly a **mechanistic causal intervention** (per the mission's own distinction) — it tests the update mechanism's sensitivity to label content, a designed perturbation — not an attempt to reconstruct an **ecologically realistic experience** (a real, naturally-occurring alternate outcome the artifact might have received under some other legitimate circumstance). Once this distinction is stated plainly, the "impossible counterfactual" concern dissolves: it is fine, and correct, for a mechanistic intervention to use a counterfactual label that could never have occurred naturally, precisely because the claim it supports ("the mechanism is/isn't sensitive to label content") is narrower than "this is what would really have happened."

**Stated as its own rule, because the two are easy to blur once a result looks clean: an artificial intervention does not need to be ecologically realizable to establish a mechanistic causal effect, but the conclusion drawn from it must be scoped to exactly what was intervened on, not generalized to what a naturally-occurring bad experience stream would do.** Estimand A can legitimately support "the update mechanism's resulting state is (or is not) sensitive to the evaluated outcome's content, holding the real experience sequence fixed" — a real, mechanistic, causally interpretable finding. It cannot legitimately support "this is how the policy would behave under a real run of degraded or adversarial experience," "the SHAM-REVERSED lineage represents a plausible alternate history," or any claim about the *rate* or *pattern* of naturally-occurring bad outcomes, because flipped labels on real artifacts are not a naturally-occurring event and the intervention was never designed to model one. Any future write-up must state the Estimand-A finding using the first phrasing and must not drift into the second — this is the specific limitation the mission's own instruction requires be carried forward, not just acknowledged once here.

**What must be frozen for Estimand A's equivalence to be interpretable**, worked through against the mission's own checklist: task (identical, from the recording), generated artifact (identical, reused byte-for-byte, never regenerated), evaluator outcome fed to `update()` (the one deliberately varied field), strategy menu (frozen, identical), features (frozen, identical — implied by an identical fixed task/strategy sequence), selector state (starts identical at `S0`, diverges only through the differing `update()` labels — this is the causal object under test), RNG state (not applicable — no new stochastic action-selection occurs under Estimand A by construction), classifier state (not applicable for the minimal lookup-table design, per §12), model outputs (identical, reused verbatim, never re-queried), update order (identical, linear replay), timestamps (must be explicitly excluded as a design constraint — the minimal selector must not use wall-clock-dependent logic, keeping this tractable), external dependencies (none, per the channel-exclusion table already in my prior design, §9/§10 there).

## 12. Complete S0/S1 state boundary

Working through Codex's own checklist against the **minimal, recommended lookup-table selector** specifically (not a generic contextual model), which materially simplifies several items by deliberate design choice rather than oversight:

| Component | Status for the minimal design |
|---|---|
| Normalization state | **N/A by design** — a discrete feature-bucket lookup table with raw incremental pass-rate means has no continuous-feature normalization step; this is a real simplification available *because* the richer contextual-model option is deliberately declined (§20 of my prior design), not something assumed away |
| Feature mappings | **Must be part of the frozen artifact** — a pure, deterministic function of (frozen extractor code hash, task text), with the granularity choice from §8 made explicit and frozen before any run |
| Classifier parameters | **N/A** — no classifier in the minimal design |
| Strategy availability | **Must be frozen and identical for `S0` and `S1`** — no strategy is ever added or removed mid-experiment; not previously stated explicitly, now required |
| Caches — backend warmth (`keep_alive`) | **A fairness/resource-matching concern (§16-17 of my prior design), not a state-boundary contamination concern** — Codex is careful to note this is not evidence of semantic memory, only a possible confound for timing/resource comparisons; classified accordingly, not conflated with the selector's own persisted state |
| Caches — the circuit breaker | **A real, separate, controllable channel — see §13** |
| Random seeds | **Must be three separately named, separately logged streams**: choice/tie-break randomness, generation (model sampling) randomness, and prospective task-order randomness. My prior design's single "matched seed per (lineage, task)" was under-specified; this is a required correction, not an addition of new scope |
| Model metadata | **Must be captured per call from the actual serving backend, not assumed from a configured constant** — `_ollama_query()` does not guarantee or expose this on its own (§13) |
| Task history | **N/A** for the stateless, single-shot generation design, except for the circuit breaker (§13) |
| External persistent state | Covered by my prior design's channel-exclusion table (§9/§10 there), now with the circuit breaker resolved from UNKNOWN to a real, named, controllable item |

**Smallest complete state boundary, stated concisely**: the persisted lookup-table file itself; the frozen feature-extractor code hash and its frozen granularity choice; the frozen strategy-menu/prompt-template hashes; a per-call, harness-verified model-digest capture; the three independently-seeded, independently-logged randomness streams; and either bypassing the circuit breaker entirely or guaranteeing one fresh process per decision. If any of these is left implicit, the `S0→S1` substitution test is uninterpretable in exactly the way Codex describes — not because the minimal design is unusually complex, but because "complete" state ownership has real, specific content that must be enumerated, not assumed from a single file hash.

## 13. `_ollama_query()` isolation audit — resolving the prior UNKNOWN

Re-traced directly this session (not merely re-reading Codex's citation): `_cb_state: dict = {}` (`app/core/echo_model_orchestrator.py:1254`) is a plain, module-level, in-memory dictionary keyed by `(model_name, task_type)`, with a 3-failure threshold and a 300-second cooldown (`_CB_THRESHOLD`/`_CB_OPEN_SECONDS`, same file, lines 1255-1256). `river_deliberation._ollama_query()` imports and calls `_cb_is_open()`/`_cb_record_success()`/`_cb_record_failure()` from this module. **This resolves my prior design's named UNKNOWN: the circuit breaker is not file-persisted and is not a learner in the persistent-across-restart sense** — a fresh process starts with an empty `_cb_state = {}`. It **does** couple calls made *within one process*: a failure on one arm's call, within one long-lived harness process, could suppress a later call to the same `(model, task_type)` for up to 300 seconds regardless of which arm makes it — a real, concrete, controllable risk, not a persistent-state concern.

**Additional, newly-identified issues from this session's own re-read of `_ollama_query()`'s signature and docstring**, not previously flagged: it accepts no explicit generation-seed parameter and returns only text, not the token/telemetry accounting my prior design assumed it could supply; a streaming failure can silently trigger a fallback through a different code path (`ollama run` subprocess) that drops the system message and does not preserve the same temperature/token-limit settings — meaning "one call, zero retries, identical request controls across every arm" is not mechanically guaranteed merely by choosing this function, and a decision that silently took the fallback path must be detected and excluded (or separately flagged), not pooled with primary-path decisions.

**Recommended repair**: call `stream_query_ollama()` directly (one layer lower in the stack) rather than `_ollama_query()`, bypassing the circuit-breaker coupling entirely, and log whichever request-construction path (`/api/chat` streaming vs. the subprocess fallback) actually served each call so a fallback-path decision can be excluded from the primary analysis. **Status: CONDITIONAL, not QUALIFIED** — the channel is now well-understood and controllable, but the controls themselves (bypassing the breaker, detecting the fallback, capturing real model digest per call) are specified, not built or verified.

## 14. Minimum preregistration repairs

Smallest delta from the existing design, classified as instructed:

**REQUIRED BEFORE IMPLEMENTATION:**
1. Rebuild the evaluator trust boundary per §4 — the single largest, most load-bearing repair; without it, nothing downstream is trustworthy.
2. Explicitly choose and freeze the feature-signature granularity (§8) before any run, specifically verifying that a T task and its corresponding S variant *can* share a signature bucket — otherwise the primary claim is unfalsifiable in the direction that would make a positive result unreachable, not merely hard.
3. Bypass the `_cb_state` circuit breaker (call `stream_query_ollama()` directly) or guarantee one fresh process per decision (§13).
4. Detect and exclude/flag any decision that silently took `_ollama_query()`'s subprocess-fallback path (§13).
5. Resolve the replay-design self-contradiction (§11) by adopting Estimand A explicitly and declining Estimand B explicitly in the written protocol.

**REQUIRED BEFORE TRIALS** (must exist before the prospective phase starts; specification/verification work, not new invention):
6. A competently-selected frozen contextual champion per a real development/validation-split selection procedure (Codex's §9), not an ad hoc hand-built router — and an explicit acknowledgment that Arm A and Arm B *may legitimately coincide* if the same architecture wins the champion competition, per Codex's own correction to my prior "A must be hand-written" framing.
7. A literal input-tuple non-overlap check across DEV/PROSPECTIVE/HOLDOUT partitions (not merely distinct seed labels) — closing the real palindrome/category_of collision risk.
8. A pilot-informed, fixed lineage count with a between-lineage variance estimate specifically (not within-task variance).
9. Prospective-phase task-order randomization, pre-registered, matched across a lineage's paired B/C twins.
10. Three independently-seeded, independently-logged randomness streams (choice, generation, task-order), replacing the prior single "matched seed."
11. Per-call, harness-captured real model-digest verification.
12. Alignment of the exclusion rule with `grade()`'s own real `infra`/`timeout` distinction — a candidate that genuinely exceeds its runtime budget is an ordinary task failure, not administrative missingness, per Codex's correction.

**CLAIM-LIMITING ONLY** (no run is blocked; the write-up's language must change):
13. NEAR-success and UNREL-ambiguity corrections to the interpretation matrix (§8).
14. State "matched final-inference cost," not "equal lifetime compute," for the fairness contract, per Codex's §8.
15. The three-way "machinery exists / is secure / is ready" distinction (§7) must appear explicitly in any future status report, not collapsed into one verdict.

**OPTIONAL:**
16. A richer contextual-model selector instead of a lookup table — still declined for the minimal version, and now additionally requiring its own normalization-state tracking (§12) if ever chosen.
17. Coarse failure-class feedback beyond PASS/FAIL — still explicitly declined; Codex agrees any additional bit requires justification this experiment does not currently have.

## 15. Singularity Archaeology ladder

Codex's own eight-rung table (their §14) is more granular and more carefully causally-gated than my prior single-jump version, and is adopted here rather than re-derived worse: repeated bounded growth → improved acquisition (a curriculum mechanism) → reusable knowledge feeding an improved acquisition mechanism → retained procedures → reusable abstraction construction → one useful acquisition → repeated acquisition without losing prior value → useful outcome-conditioned selection → **acquisition beyond a fixed action menu** → existing state/selection machinery → **causally useful retained outcome-conditioned selection** → existing logs/persistence → identified behavioral consequence. Every rung, in Codex's own framing (correctly, and consistent with the mission's "no magical arrows" instruction), requires its own mechanism, state change, observable consequence, and falsification test — none is a free inference from the rung below it.

## 16. First unsupported arrow

Adopting Codex's more precise phrasing over my own prior, less exact version: **correctly attributed, independently verified experience causes a retained selection change that improves later task correctness beyond competent frozen routing, at matched cost.** "Correctly attributed" and "matched cost" are the two words my own prior phrasing lacked and needed.

## 17. Next unsupported arrow, if the first is established

**Useful outcome-conditioned selection among a fixed menu → acquisition of a genuinely new, independently-validated procedure not already present in that menu.** This matches, in substance, what my own prior design's §21 already named (the missing capability being strategy generation and representation expansion) — restated here in Codex's cleaner, ladder-consistent phrasing rather than reworded for its own sake.

## 18. Strongest skeptical interpretation

Adopted directly from Codex's own §16, because independently re-deriving a weaker version would serve no purpose:

> The study demonstrates, at most, calibration of a fixed solver portfolio on a small authored template ecology. Its "novel" tasks reuse generator structure, recognizable wrappers, and native programming skills. A persistent signature table can select better pretrained behavior without developing any new abstraction or acquisition ability. Restarting a client does not isolate historical error prompts, classifier state, reflected scores, caches, or backend state. Logged updates and hashes do not establish that evaluated outcome content caused the improvement. Most seriously, the proposed hidden evaluator places expected answers in the candidate's own runtime module and returns failure diagnostics containing expected values. Higher hidden-test pass rates therefore need not mean higher task correctness.

**What survives this skepticism, once the §4/§14 repairs are actually built and independently verified (not merely specified)**: a bounded, bookkeeping-honest claim that a standalone selector's retained, evaluated experience causally changed which of several fixed strategies it chose, in a way that improved measured, genuinely-hidden correctness beyond a competent frozen router and an identical non-updating twin — with a persistent lookup table over pretrained-strategy outcomes named explicitly, throughout, as an admissible and equally legitimate explanation of that same result, not a competing hypothesis to be argued away.

## 19. Remaining blockers

- The evaluator trust boundary is specified (§4) but not built or independently verified.
- The feature-signature granularity choice (§8) has not been made.
- The circuit-breaker bypass and fallback-path detection (§13) have not been implemented.
- The replay design has not been re-written to adopt Estimand A exclusively in the actual protocol document (this report specifies the fix; the design document itself still contains the contradiction until edited).
- No competently-selected frozen champion, partition-disjointness check, pilot variance estimate, task-order randomization, three-way seed split, or per-call digest capture yet exists.
- AP-0's own live qualification-gate result files (cited by Codex as showing an incomplete gate) were not independently re-verified in this pass — flagged as UNKNOWN, not assumed either way, and not load-bearing for any verdict here since my design never depended on that specific run succeeding.

## 20. Final recommendation

**Verdict: B — the protocol is repairable with small, specified changes.** The core architecture — a standalone selector isolated from live Echo, a fixed strategy menu, AP-0's task-construction machinery, three arms, and the four causal interventions — survives every attack in this pre-mortem intact; nothing here requires abandoning it. What is required is: one bounded (if real) restructuring of an existing mechanism (§4), one previously-implicit design choice made explicit (§8), one function-call substitution plus exclusion logic (§13), one resolved internal contradiction (§11), and a set of statistical/fairness specifications that sharpen rather than replace what was already there (§10/§14). None of Codex's findings show the underlying research question to be unaddressable with this substrate — every one of them shows a specific, nameable gap in how it was currently specified. **This is not verdict A** (the current protocol does not survive unmodified — the evaluator flaw alone rules that out) **and not verdict D or E** (nothing here shows the boundary is fundamentally unresolvable or that the substrate cannot support the claim — a concrete, reuse-based repair is specified for every gap found). Implementation remains not authorized.

---

**CODEX EVALUATOR ATTACK:** CONFIRMED

**CANDIDATE/EXPECTED-ANSWER SEPARATION:** INSUFFICIENT

**JAIL ISOLATION:** CONDITIONAL

**LEARNER FEEDBACK BOUNDARY:** CONDITIONAL

**TASK CORRECTNESS:** NOT QUALIFIED

**BOUNDED LEARNING CLAIM:** CONDITIONAL

**EXPERIMENTAL UNIT:** HISTORY

**REPLAY INTERVENTION:** CONDITIONAL

**S0/S1 STATE BOUNDARY:** PARTIAL

**OLLAMA GENERATION ISOLATION:** CONDITIONAL

**PREREGISTRATION REPAIR:** SMALL

**FIRST UNSUPPORTED ARROW:** Correctly attributed, independently verified experience causes a retained selection change that improves later task correctness beyond competent frozen routing, at matched cost.

**NEXT UNSUPPORTED ARROW:** Useful outcome-conditioned selection among a fixed menu of existing strategies causes acquisition of a genuinely new, independently-validated procedure not already present in that menu.

**READY FOR IMPLEMENTATION:** NO

**1. Could the current evaluator let a candidate obtain the answer without solving the task? If so, exactly how?** Yes. `oracle_runner.grade()` concatenates candidate code with `make_test_code()`'s output — which defines `_CASES = [(args, expected), ...]` as a bare module-level global — into one file, executed as one Python module with one shared global namespace. A candidate function, once called by the test loop, can reference the bare name `_CASES` (ordinary name resolution, no special technique) and return the expected value for its own arguments directly, scoring a legitimate-looking PASS with zero real task-solving logic.

**2. What is the minimum trusted boundary required to prevent that?** Candidate execution and expected-value storage/comparison must occur in separately-trusted OS processes, not merely separate namespaces within one process (which remains vulnerable to frame introspection). Run the candidate in its own sandboxed subprocess receiving only permitted inputs and emitting only its computed output; hold `_CASES` and perform the comparison in a separate, trusted controller process that the candidate's own process never runs inside or can read into.

**3. If the repaired experiment succeeds perfectly, what is the strongest learning claim we can legitimately make?** A bounded, standalone selector used retained, independently-verified evaluated experience to cause a persistent, restart-surviving change in which of several fixed strategies it chose for structurally-related-but-non-identical tasks, improving measured hidden-task correctness beyond both a competent frozen router and an architecturally identical non-updating twin, at matched final-inference cost.

**4. What weaker mechanism could still explain that success?** A persistent, finite lookup table mapping task-feature signatures to per-strategy outcome statistics, refined by ordinary count-based estimation, that never proposes a new strategy and never changes its own feature representation — a complete, legitimate instance of the same bounded claim, not a refutation of it, but indistinguishable from "genuine learning" using only the interventions specified here, and must always be named as an equally admissible explanation, never argued away.

**5. What is the next developmental capability we would need to test after bounded persistent routing improvement?** Whether experience can cause acquisition of a genuinely new problem-solving procedure not present in the system's original fixed strategy menu — not merely better selection among strategies it already had.
