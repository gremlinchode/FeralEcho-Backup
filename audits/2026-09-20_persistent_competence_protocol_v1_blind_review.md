# Blind Adversarial Review — Persistent-Competence Frozen Protocol v1.0

**Date:** 2026-09-20
**Reviewer posture:** fresh session, no prior involvement in the protocol's lineage; the protocol was treated as written by investigators motivated to obtain a positive result. Review is read-only. No experiment was implemented or run. No model was called.
**Independence method:** direct review by a fresh session (no prior involvement in the mission being reviewed). Not a multi-agent review; treat as one independent reader, not a panel.
**Evidence labels:** **OBSERVED** = read directly in the protocol/source or measured by me this session. **INFERRED** = follows from OBSERVED facts by reasoning I state. **UNKNOWN** = not established.

---

## 0. Integrity record (before)

```
Git HEAD (before):            2fba42644c82b9f7096276f4dd338d615cf1bcce
Working tree (before):        177 changed/untracked paths (git status --porcelain), snapshot saved to session scratchpad
Protocol .md sha256 (before): d1968caf5360e60b8b8d9ca0db9769de4f8bea518ca537a73ea00b8fa5898c06  == frozen value  (MATCH)
Protocol .json sha256 (before): b35ad16b3c0fed878d74ff404f00892a6be66a8227211510b79e77e50db18131 == frozen value  (MATCH)
Review report existed before:  no
```

(After-state recorded in §9.)

---

## 1. Bottom line

**OBSERVED:** the protocol is carefully built against the *previous* proposal's known failure classes (answer-key leakage, environment inheritance, singleton state, per-arm grader drift, partial ablation ladders). Those defenses mostly hold (§6).

**The problem is that it is careful about the wrong layer.** The oracle is hardened, but the *experimental logic that sits on top of it* — the selection metric, the frozen tie-break, and the sham/transplant construction — is such that a conformant implementation can earn positive labels from **a fixed worker-quality gap plus a hand-typed number**, with no learned competence in any sense. I constructed such an execution (§4) and checked its mechanics with a synthetic simulation of the protocol's own stated semantics (§4.3).

**Verdict: V1.0 REQUIRES REVISION** (final line of this document).

---

## 2. What "correct-selection" actually is (a premise the whole analysis rests on)

**OBSERVED (protocol lines 20–29):** the only definition of the metric is in the notation paragraph: a *selection trial* is one held-out task where "the system picks whichever of two candidate workers has the higher `score()` for that capability," "scored via the oracle." **INFERRED reading:** "correct" = the picked worker's completion passes the oracle. The term "correct-selection" is never defined separately. (If the intended meaning is different — e.g. "picked the truly better worker" — the protocol does not say, and that is itself a defect; see V10.)

**OBSERVED (Final Adversarial Check #6, line 420; JSON `carrier_schema.tie_break_rule`):** score ties are broken **alphabetically by `worker_id`**.

**OBSERVED (python, this session):** `sorted(["qwen2.5-coder:7b","llama3.2:3b","deepseek-r1:7b"])` → `['deepseek-r1:7b', 'llama3.2:3b', 'qwen2.5-coder:7b']`.

**INFERRED consequences** (these drive V1, V2, V8):

1. Arm A (all scores 0.5) does **not** choose randomly. For the primary pair (qwen vs llama) it deterministically picks `llama3.2:3b`. A's "correct-selection rate" is just llama's pass rate.
2. Arm B (qwen learns; llama stays cold at 0.5) picks qwen iff `mean_qwen > 0.5` (with count ≥ 5). B's rate is qwen's pass rate. So **H1's "gain" = (qwen pass rate − llama pass rate) on EVAL**, whenever qwen's TRAIN mean exceeds the 0.5 neutral prior.
3. `deepseek-r1:7b` sorts before both other primary workers. In arm D/S1 (recipient = deepseek), deepseek wins any tie and wins whenever its transplanted mean ≥ 0.5. A cold, untouched deepseek would also win. **The transplant changes nothing about who is selected.**

---

## 3. Verification of the protocol's assumptions about existing infrastructure

| Protocol assumption | Status | Evidence |
|---|---|---|
| §3a: the F2 sandbox "reused unmodified", incl. `run_sandbox_script_isolated()`, with explicit `env=` allowlist, pinned `PYTHONHASHSEED`, custom profile | **PARTIALLY FALSE (OBSERVED)** | `sandbox/run_script.py:171` — signature is `(script_path, timeout)`; no `env`, profile, or seed parameter; `subprocess.run(...)` passes no `env=` (inherits parent env) and `cwd=os.getcwd()`. Reuse is limited to `safe_exec_wrapper.py`; the runner and profile must be new code. |
| §3b.2: solver profile is default-deny with reads scoped to "exactly three subtrees" | **Infeasible as literally stated (INFERRED)** | Existing `sandbox/echo_sandbox.sb:28` is global `(allow file-read*)`. `safe_exec_wrapper.py:509-510` inserts the repo root into `sys.path` and the wrapper itself lives in the repo; a solver process cannot start without reading the wrapper (outside the "three subtrees"). Implementer must widen read scope at implementation time, discretionarily. Q1 partly catches over-widening. |
| §2a: mirrors `behavioral_state.py` atomic write, `self_model_claims.py` no-cache read | Files exist (OBSERVED) | `app/core/behavioral_state.py`, `app/core/self_model_claims.py` present. Contents not re-audited (prior reports' claim; not needed for this review). |
| §2a: `MIN_OBSERVATIONS=5` matches RiverBrain's gate | **OBSERVED true** | `echo_model_orchestrator.py`: `_MIN_MODEL_OBSERVATIONS = 5`, `_MEAN_EFFECTIVE_WINDOW = 200`. |
| §6.3: baseline hashes of `memory/river_brain.pkl`, `task_type_classifier.pkl`, `self_model_claims.jsonl`, `behavioral_directives.json` | Files exist (OBSERVED) | The live server autosaves `river_brain.pkl` continuously; "re-captured after, to prove non-contamination" is uninterpretable unless the server is stopped (V11). |
| Protocol's rules for tie-break, exclusion cap, single pilot, grader-hash "are now part of §2a/§3b/§16/§17" (line 425) | **FALSE (OBSERVED, grep)** | `alphabetical` appears only at line 420; `10%` only at 421; grader content-hash only at 419. None appear in §2a, §3b, §16, §17. They exist only in the "Final Adversarial Check" section (and, for the tie-break, the JSON). |
| §7: "A's `score()` always returns 0.5 so selection is effectively random" | **FALSE given the frozen tie-break (OBSERVED)** | See §2. The power calculation's p₁=0.50 premise is therefore wrong. |
| MD vs JSON agree on which workers learn | **CONFLICT (OBSERVED)** | MD §4: only `qwen2.5-coder:7b` learns; llama is "a fixed comparison point". JSON `workers.trained` lists both `qwen2.5-coder:7b` and `llama3.2:3b`. |

---

## 4. Complete adversarial execution (E1)

**Result of the attempt: I can construct one.** Conditional on empirical worker behavior that I did **not** measure (UNKNOWN — no model was run), the execution below is fully conformant with v1.0 text, passes the apparatus gate, and earns a positive label with no learned competence.

### 4.1 Preconditions (the only empirical assumptions)

- (P1) On `EVAL` and on transfer cell 5, `qwen2.5-coder:7b` outperforms `llama3.2:3b` by ≥ 15pp for each trained capability. **INFERRED plausible** (a 7B code model vs a 3B general model on simple Python tasks), **UNKNOWN** in fact.
- (P2) qwen's pass rate on `TRAIN` > 0.5 (so its mean exceeds the 0.5 neutral). The implementer authors the task generator (V3), so this is under implementer control.
- (P3) For H3: deepseek-r1:7b passes EVAL within ±10pp of qwen, *or* beats llama by ≥ 50% of B's gain with significance. **UNKNOWN**; the implementer's unspecified prompt/extraction/token-budget choices (V3) influence it — a reasoning model's think-tokens can also *hurt* it, so this is the least certain link.

### 4.2 Walk-through

1. **Apparatus gate.** §6 preflight and Q1–Q12 exercise isolation and grading of synthetic candidates. None involve worker selection. **PASS** with a correctly built harness. (OBSERVED: nothing in Q1–Q12 references tie-break or selection.)
2. **Stage 2 pilot.** 8 episodes, 10 EVAL tasks: D's raw count differs from A's by ≥ 1 → "wiring OK" → scale. (Also see V3: the pilot runs on EVAL tasks.)
3. **A**: all ties → llama. **A′**: identical (ties → llama). **B**: `learn()` 60× on qwen → mean ≈ qwen's pass rate > 0.5 → picks qwen. **H1**: B beats A by the gap, exact McNemar p ≪ 0.05, gain ≥ 15pp. ✅
4. **C** (reset qwen's cell): ties → llama → exactly A's selection. C vs B significant regression ✅; C vs A no significant difference ✅. **H2 passes** — and passes for the trivial reason that resetting a cell returns the selector to "always llama."
5. **D/S1** (deepseek recipient; transplant mean ≥ 0.5): picks deepseek — same as a *cold* deepseek. **H3** passes via TOST D≈B or via D vs A if deepseek ≥ llama by the required margin. ✅ (conditional on P3)
6. **H5 (cell 5):** same key → same selection → same worker gap on a different template family. ✅
7. **Cells 6/7 (negative controls):** untrained keys → every arm ties → alphabetical → B ≡ A exactly. Null, so nothing is flagged as a confound. ✅ (V8)
8. **H6:** selection is constant after round 0. If per-task completions are cached/reused (protocol silent, V6), every retention cell equals its baseline → no drop → passes. ✅
9. **H4 (poisoned E):** E's inverted mean = 1 − p_deepseek < 0.5 when deepseek passes > 50% → picks llama = A's selection → E is *not* below A → **H4 fails**. But H4 is explicitly non-label-determining (§15, last paragraph): "flagged inconsistency requiring explicit discussion," no downgrade. **The label stands.** (V5)
10. **H7 / sham:** S1 and D produce identical selections → D≈S1≈S2 → §5 pre-registers this as *support* for sufficiency.
11. **Label:** REUSABLE TRANSFER (H6 not run/failed) or **ACCUMULATED COMPETENCE CONSISTENT WITH EVIDENCE** (H6 via the caching lever) — with a footnoted H4 failure.

**What actually happened:** a fixed worker-quality gap was measured, and a number > 0.5 was written to and read from a JSON file. No competence was acquired by anything.

### 4.3 Supporting simulation (OBSERVED, mine; synthetic — not FeralEcho behavior)

`sim_v1.py` (session scratchpad, not committed) implements the protocol's *stated* semantics — `score()` = 0.5 if count<5 else mean, alphabetical tie-break, arms A/B/C/D and a cold-recipient D0 — over **hypothetical** Bernoulli workers (qwen 0.80, llama 0.55, deepseek 0.75; these rates are assumptions, not measurements). N=60, exact one-sided McNemar.

- Selections in every run: `A→llama, B→qwen, C→llama, D→deepseek, D0(cold)→deepseek`. **The transplanted recipient and the never-touched recipient select identically.**
- **Null implementation** — no `learn()`, qwen's cell hand-typed to `{count:5, mean:0.51}`: selections identical to the "real learning" run in every arm. H1 pass rate over 2000 simulated runs: **0.877 (real `learn()`) vs 0.869 (hand-typed carrier).** The learned value is not doing the work.
- **Sanity control:** with equal workers (all 0.70) H1 passes only 3.2% of runs — the test is not trivially passing; it is passing on the worker gap, as claimed.

---

## 5. Vulnerabilities

Format per item: provision · false-positive scenario · exploitable while conformant · severity · minimum change.

### V1 — CRITICAL — H1/H2/H3/H5 reduce to a fixed worker-quality gap; A is a deterministic always-llama policy
- **Provisions:** §1 line 20 (metric definition); §4 (only qwen learns; llama "fixed comparison point"); §7 (A "effectively random"); Final Adversarial Check #6 (alphabetical tie-break); JSON `carrier_schema.tie_break_rule`.
- **Scenario:** §4.2 steps 3–6. Gain = qwen − llama pass rate; B's "learning" need only push one mean above the 0.5 neutral prior, which is also the selection boundary. A hand-typed 0.51 does the same (§4.3).
- **Conformant exploit:** Yes. Every step is a literal reading of v1.0. The tie-break rule was added specifically to close cheat #6 ("smuggle learning into the tie-break") and instead made the *baseline* deterministic and worker-dependent.
- **Also:** §7's power calculation (A ≈ 0.50) is wrong under this rule, so N_eval=60 is justified by a false premise.
- **Minimum change:** (a) replace the alphabetical tie-break with a per-task pre-registered seeded coin, identical across arms (or score A analytically as the mean of both workers' per-task pass indicators); (b) add a **constant-policy arm K** (always the worker that is best on a disjoint calibration set) and a **hand-written-carrier arm**, and require H1 to hold against the *better* of A and K; (c) preferably use a **crossover design** — a calibrated pair where worker superiority *reverses* across capabilities, with both workers trained — so no fixed worker preference reproduces B's gain; (d) report raw per-worker pass rates on every partition.

### V2 — CRITICAL — the sham/transplant logic cannot detect anything: D ≡ S1 by construction, and the transplant is inert under the tie-break
- **Provisions:** §4 rows D and S1; §5; §1 H3; §11 L0–L8.
- **OBSERVED:** D's procedure ("fresh carrier… `_write_carrier()` sets exactly the `list_aggregation` cell to B's `{count, mean}`… re-keyed under deepseek") and S1's procedure ("fresh carrier… one `_write_carrier()` call setting `list_aggregation` to **B's exact post-learning `{count, mean}`**… re-keyed under deepseek") are the same operation with different names. §5 itself acknowledges divergence "would be surprising given `score()`'s pure-function definition."
- **Scenario:** §4.2 steps 5, 10; §4.3 (D and cold D0 select identically). **No cold-recipient control (D0) exists among the arms**, and D's comparison pair is never stated (the protocol defines arms "over the primary comparison pair" qwen-vs-llama, yet D's carrier is keyed to deepseek). For any partner among the fixed workers, deepseek wins ties, so the transplant cannot change selection for mean ≥ 0.5. H3's second branch ("D vs A significant at ≥ 50% of B's gain") then measures deepseek-vs-llama quality, again a worker gap.
- **Conformant exploit:** Yes; §5 pre-registers D≈S1≈S2 as *supporting* sufficiency, so the fabricated-number arm agreeing with the "earned" arm is scored as a pass.
- **Minimum change:** define D's comparison pair explicitly; add **D0** (cold recipient, same pair, same tie-break) and require H3 to test **D − D0**; add **neutral-value** (`mean=.5,count=60`) and **inverted-value** transplants (S3/S4) that must *not* produce the effect; either drop S1 or make it differ from D in a way a consumer could see; delete the statement that D≈S1 supports H3/H7 unless D − D0 is established.

### V3 — HIGH — large post-freeze implementer discretion over the quantities that determine the outcome
- **Provisions:** §8 (tasks generated "at implementation time"; hashes appended as a permitted addendum, §18a); §16 Stage 2 (pilot on 10 **EVAL** tasks; "STOP, debug"); §18 (harness bug fixes permitted without a new version); §8 EVAL "≥ 60" (no fixed upper N).
- **OBSERVED (grep of the protocol):** zero mentions of **temperature, sampling, `num_predict`/token cap, think-token handling, code-extraction/cleanup function, prompt template, or worker timeouts.** Also unspecified: arm execution order/interleaving, and completion caching.
- **Scenario:** the outcome of V1 is a function of exactly these unspecified items (P1–P3). An implementer can, without breaking a frozen rule, tune the prompt/extraction/token budget to favor qwen and deepseek, author easy TRAIN and hard EVAL families, and iterate during the pilot's "debug" step using EVAL tasks. The pilot's EVAL tasks are not stated to be excluded from the final EVAL set.
- **Conformant exploit:** Yes — these are all outside the frozen list of "protocol elements."
- **Minimum change:** freeze by hash, in a pre-registration commit made **before Stage 2**: generator code, templates, reference solutions, prompt template, decoding parameters, extraction function, timeouts, arm run-order rule, completion-cache policy; give the pilot its own disjoint `PILOT` partition; fix `N_eval` as an exact number.

### V4 — HIGH — re-rolls via version bumps; no cumulative disclosure; self-attested evidence
- **Provisions:** §18 ("requires a new protocol version… created BEFORE examining any affected experimental outcome"; protocol deviation ≠ experimental failure); Final Adversarial Check #4 (a second pilot = deviation "requiring a version bump"); §17 (harness git hash "once implemented"; ledger written by the harness).
- **Scenario:** a failed Stage-3 run is recharacterized as "the instrument needed adjustment" (the §18 example — worker-specific timeouts — is exactly such a case), v1.1 is issued, and the experiment is re-run until it passes. The "created BEFORE examining any outcome" condition cannot be satisfied by a deviation *discovered from* an outcome, and nothing forbids doing it anyway. There is no rule that all runs of all versions must be reported, and no requirement that the harness/grader be committed and hashed before data collection. The conformance check (#9) is authored by the implementer.
- **Conformant exploit:** Yes.
- **Minimum change:** one full-scale run per pre-registered hash; every run of every version must be reported together; a version bump after any Stage-3 data exists forfeits eligibility for the top two labels; harness + generator + grader committed and hashed pre-Stage-2; evidence directory hash-chained; conformance exhibit produced by a party other than the harness author (the Integrity Record itself concedes only self-review occurred).

### V5 — HIGH — label logic lets the protocol's own sanity checks fail without consequence; H2/H3 "or" branches are toothless
- **Provisions:** §15 final paragraph (H4/H7 "not label-determining"); §1 H2 ("no remaining significant difference, **or** residual gain < 7.5pp"); §1 H3 ("**or**, failing equivalence, D vs A significant at ≥ 50% of B's gain").
- **Scenario:** H4 (poison must degrade) fails structurally under the tie-break (E = A, §4.2 step 9) and the label is unchanged. H2's first branch is absence-of-significance at N=60, which passes with a real residual effect of ≈ 10–14pp. TOST at ±10pp with N=60 is underpowered, so H3 is effectively decided by the "or" branch, which is ambiguous ("significant at ≥ 50%" — significant *and* ≥ 50%, or significantly ≥ 50%?).
- **Conformant exploit:** Yes.
- **Minimum change:** H4 failure and any D/S divergence must **cap** the label (e.g. at PERSISTENT ADAPTATION ONLY); H2 requires an equivalence test (C ≈ A) or only the < 7.5pp branch; define H3's second branch unambiguously.

### V6 — HIGH — H6 is either vacuous or unpassable, and the label name claims more than H6 can show
- **Provisions:** §1 H6; §7 (carrier's mean cannot distinguish accumulation/averaging/single-batch); §10 (retention cells; "(c) EVAL must show improvement round over round"); §15 (`ACCUMULATED COMPETENCE…` requires H6).
- **OBSERVED contradictions:** (i) §10 calls prior-round blocks "held out and never re-trained on", but those tasks *were* trained on at round *i* (§10's own schedule). (ii) The formal H6 row and falsification condition contain only the no-drop test; the "(c) rising EVAL" requirement appears only in prose. Under a threshold selector, EVAL performance cannot rise after the mean crosses 0.5, so if (c) is required H6 is unpassable for a legitimate carrier; if not, H6 is satisfied by any constant policy.
- **Conformant exploit:** Yes — caching per-(worker,task) completions across rounds makes every retention cell equal its baseline (no drop, vacuous pass); regenerating instead makes H6 fail from sampling noise alone (δ = 1 SE of a single n=20 binomial, six cells) — the protocol does not say which, so the implementer chooses the outcome.
- **Minimum change:** fix and hash the completion-cache policy; use fresh held-out blocks per round; make (c) a formal, testable clause or delete it; add a pre-registered non-monotone experience schedule with exactly predicted carrier trajectories (distinguishing cumulative-mean from overwrite), or rename the top label so it does not assert "accumulated."

### V7 — MEDIUM — no aggregation rule across replications; no multiplicity control
- **Provisions:** §4 (three trained capabilities as "pre-registered replications"); Final Adversarial Check #1 ("does not permit averaging across capabilities to rescue a failing one"); §15.
- **Scenario:** the labels are stated in terms of "H1 passes" without saying for which capability or how many of three. The primary capability alone can carry a label; ~5 one-sided tests × 3 capabilities are run at α=0.05 with no correction.
- **Exploitable:** Yes (label on `list_aggregation` alone; report the best of three).
- **Minimum change:** require all three (or a stated Holm-corrected rule) for any label above FAIL; state which is primary and that a failed replication caps the label.

### V8 — HIGH — the "negative controls" are structurally blind (cells 6 and 7 / recursion_base_case / date_arithmetic)
- **Provisions:** §9 cells 6, 7; §8 capability list.
- **OBSERVED/INFERRED:** unlike cell 4, cells 6 and 7 are presented as informative. But their carrier cells are untrained in every arm, so every arm ties and the alphabetical rule makes B ≡ A. A B>A effect there is impossible; the confound alarm ("blocks any H5/H6 claim") can never fire, *including* when the real cause of B's gain on trained capabilities is a global worker advantage.
- **Exploitable:** Yes — the control cannot disagree with the result.
- **Minimum change:** additionally report raw worker-vs-worker pass rates on every family including cells 6/7; require B's gain on trained capabilities to exceed what a constant-worker policy achieves (ties into V1's arm K).

### V9 — MEDIUM — nondeterminism and exclusion handling
- **Provisions:** §3b.8 (dual `PYTHONHASHSEED` runs); Final Adversarial Check #7 (10% cap); §1/§7 (N_eval ≥ 60 required for H1).
- **Observations:** dual-seed agreement re-executes the *same* completion under two hash seeds; it addresses hash-order dependence only. Generation stochasticity is unspecified (no temperature, no repeat sampling), so per-task outcomes are single draws regenerated independently per arm. Exclusions are by (worker-dependent) hash-order sensitivity, so they change each worker's effective pass rate unevenly; the cap applies to `EVAL` per arm but `TRAIN` exclusions (which decide what enters the carrier) are uncapped. The 10% cap also conflicts with `N_eval ≥ 60` unless EVAL is oversized (which V3's unbounded "≥ 60" permits at will).
- **Exploitable:** Marginal, but available.
- **Minimum change:** specify decoding parameters and one fixed sampling policy; cap and log exclusions per worker and per partition (TRAIN included); fix EVAL size so the cap and N floor are jointly satisfiable.

### V10 — MEDIUM — normative ambiguity and internal inconsistency
- **Observations (all OBSERVED):** the tie-break, exclusion cap, single-pilot rule and grader-hash requirement live only in the "Final Adversarial Check" section, while line 425 asserts they are "now part of" §2a/§3b/§16/§17 (they are not). MD/JSON disagree on which workers are trained. `correct-selection` is defined only inside a notation paragraph. No precedence rule between MD and JSON, or between numbered sections and the adversarial-check section.
- **Exploitable:** an implementer who reads only the numbered sections omits the tie-break and cap; one who wants latitude can call the adversarial-check section non-normative.
- **Minimum change:** move every rule into a numbered section, mirror it in the JSON, state MD-over-JSON (or the reverse) precedence, define the metric formally, reconcile "trained" workers.

### V11 — MEDIUM — sandbox specification is not implementable as written; several battery items are inspection-only
- **Provisions:** §3a–3c; Q3, Q4, Q10; §6.3/§6.8.
- **Observations:** §3 above. Q10 is verified "by confirming the harness code path is identical" — a code-inspection claim, not a behavioral test. Q1–Q10 use synthetic candidates; the real solver is an LLM whose failure modes (not adversarial file search) drive results. The production-hash non-contamination check (§6.3) is uninterpretable while the live server autosaves.
- **Exploitable:** low direct false-positive power (Q1 and the read-scope check would catch gross leakage), but the implementer must make unspecified widening decisions.
- **Minimum change:** specify the exact read-allow set (including wrapper path), require the gate to fail closed if the profile is widened beyond a hashed list, and require the FeralEcho server and autonomous loops to be stopped during runs (or hash-diff only files the run could touch).

### V12 — LOW/MEDIUM — shared Ollama and unscheduled arm ordering
- **Observation:** all arms use the same Ollama server; nothing requires the production Echo (which runs its own autonomous multi-model loops) to be quiescent, nor arms to be interleaved or order-randomized. Timeouts under load hit whichever worker/arm is running then. Because A ≡ always-llama and B ≡ always-qwen (V1), any time-correlated timeout pattern maps directly onto "worker gap."
- **Minimum change:** stop production loops for the run; interleave arms per task in a pre-registered randomized order.

---

## 6. Attacks that failed (real positive evidence)

I tried each of these against v1.0 and could not break them *as written*:

1. **Answer-key visibility through a shared parent directory / discoverable path.** Prompts and answers are in physically separate directories, graded in a separate process afterward, with Q1 porting the demonstrated exploit. The structural design is sound; only its implementability (V11) is doubtful.
2. **Cross-arm state sharing / singleton resurrection (the RiverBrain hazard).** Per-arm filesystem roots, per-arm subprocesses, plain-file carriers, static import audit. I found no path for one arm's mutable state to reach another's.
3. **Per-arm grader leniency.** The shared grading-function hash closes it (though it exists only in the adversarial-check section, V10).
4. **Partial ablation ladder.** "All nine rows or no H7 finding" closes cherry-picking a stopping level.
5. **Silent NaN/`nondeterministic`→pass coercion.** Explicitly excluded and logged; cap exists (V9 notes limits).
6. **Order sensitivity of the carrier mean.** §7's derivation is correct (cumulative mean is order-invariant), and the protocol says so honestly rather than claiming order tests it cannot run.
7. **Overclaim in the Claim Boundary.** The protocol is careful to say it would only show a *constructed pathway*, never that FeralEcho already has competence. That honesty is genuine; V1/V2 are about whether even the narrower claim is earned.

---

## 7. Consolidated minimum revision (v1.1)

1. Replace alphabetical tie-break with a seeded per-task coin identical across arms; correct §7's power analysis.
2. Add a constant-policy arm and a hand-written-carrier arm; require B to beat the better of A and K; prefer a calibrated **crossover** worker-pair design with both workers trained.
3. Add D0 (cold recipient) and neutral/inverted transplants; define D's pair; H3 tests D − D0.
4. Freeze generator, templates, prompts, decoding, extraction, timeouts, cache policy, run-order in a pre-registration commit before Stage 2; separate `PILOT` partition; exact `N_eval`.
5. Cumulative reporting of all runs/versions; one full-scale run per hash; harness/grader hashed pre-data; independent conformance exhibit.
6. H4 and D/S divergence become label-capping; H2 needs equivalence; H3's branches made exact; multiplicity/replication rule stated.
7. Formalize or drop H6's clause (c); use fresh held-out blocks per round; or rename the top label.
8. Report raw per-worker gaps on every family so negative controls can actually fire.
9. Move all closures from the adversarial-check section into numbered sections and the JSON; state precedence; define the metric.
10. Make the sandbox spec implementable and hashed; stop production loops during runs.

---

## 8. What remains UNKNOWN

- The actual qwen/llama/deepseek pass rates on any task family here. E1 is conditional on them (P1–P3). I ran no model.
- Whether an implementer following v1.0 would, in fact, choose the exploitable readings — this review establishes availability, not intent.
- Whether the intended meaning of "correct-selection" is different from my inference (§2); if so, V1/V2's mechanics change and the metric itself must be stated.

---

## 9. Integrity record (after)

```
Git HEAD (after):               2fba42644c82b9f7096276f4dd338d615cf1bcce   (unchanged)
Working tree (after):           178 paths; the only difference from the "before" snapshot is this report
                                (?? audits/2026-09-20_persistent_competence_protocol_v1_blind_review.md)
Protocol .md sha256 (after):    d1968caf5360e60b8b8d9ca0db9769de4f8bea518ca537a73ea00b8fa5898c06  (byte-identical to before)
Protocol .json sha256 (after):  b35ad16b3c0fed878d74ff404f00892a6be66a8227211510b79e77e50db18131  (byte-identical to before)
Commits / pushes / restarts:    none
Production code, config, persistent state, model state, Git history: not modified
Model calls made:               none
Scratch artifacts:              sim_v1.py, status_before.txt, status_after.txt — session scratchpad only, outside the repo
```

## Verdict

**V1.0 REQUIRES REVISION**

**Single strongest reason:** the frozen alphabetical tie-break makes arm A a deterministic always-llama policy and lets an untouched deepseek win every tie, so H1/H2/H3/H5 measure a fixed worker-quality gap and a zero-effect transplant — and because D and S1 are the same construction and no cold-recipient, constant-policy, or hand-written-carrier control exists, a hand-typed `mean=0.51` earns the same labels as real learning, with no arm in the protocol able to tell the difference.
