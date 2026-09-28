# Adversarial Review: Persistent-Competence Experiment Design (2026-09-19)

**Date:** 2026-09-19
**Type:** Independent adversarial review (read-only; no code, config, learning state, or git history touched)
**Subject:** `audits/2026-09-19_persistent_competence_experiment_design.md` and its evidence ledger
**Method:** Four genuinely independent, non-fork reviewer agents, each briefed only on the target report + evidence ledger + this project's `feral-independent-review` reviewer checklist — none saw the original mission's reasoning, none saw each other's work, none were forks of the session that authored the report under review. This document is a faithful compilation of their four reports, not a re-judgment of them. Where the compiler (this session, the original report's author) added anything beyond mechanical assembly, it is marked `[COMPILER NOTE]`.
**Reviewer threads, referenced below by ID:**
- **R1** — RiverBrain-uniqueness re-search (Attack 1)
- **R2** — Novel-transfer matrix, accumulation attack, apparatus false-positive catalog (Attacks 5, 6, apparatus)
- **R3** — A/B/C/D confounds, Lizard-Tail amputation, second-generation transfer (Attacks 3, 7, 8)
- **R4** — Evaluator independence, poisoned-experience design (Attacks 2, 4)

---

## 1. Executive Verdict

**The Sept 19 report's narrow, literal claim — that RiverBrain's `learn() → model_task_stats → score_model() → council ranking` chain has a VERIFIED causal link from state mutation to a changed selection decision — survives independent re-derivation intact** (R1, R3). Nothing in this review contradicts that specific claim.

**Everything built on top of that claim — the proposed experiment as a mechanism for demonstrating genuine competence — does not survive as specified.** Four independent reviewers, working from the artifacts alone, converged on a consistent picture: the report's architecture is directionally sound but contains **one working exploit** that would let a system pass the proposed experiment's entire falsification battery without acquiring any real capability (R4), **one internal self-contradiction** in its own Step 1 (R2), **at least three unaddressed state-isolation hazards** that risk contaminating live production data or silently producing a false result (R3, independently reconfirmed in part by R4), **a mathematical identity** that makes the proposed longitudinal and second-generation designs uninformative below a specific, unstated observation-count threshold (R2, independently reconfirmed by R3 from a different angle), and **a literal example in its own novel-transfer test that is guaranteed to return a null result regardless of any real transfer property** (R2). Separately, the report's central uniqueness claim ("one mechanism") is **too strong as written** — two real, live-wired mechanisms exist that the original investigation never found (R1).

None of these findings overturn the report's core architectural direction. All are fixable, all are named with a specific, concrete fix below, and several (R3, R4's Tier-8 singleton-contamination finding) were found **independently by two separate reviewers using different methods**, which is itself the strongest form of corroboration available to this methodology.

---

## 2. Strongest Falsification of the Sept 19 Proposal

Ranked by how directly each one would let a **false positive** survive the proposal's own falsification criteria (§11 of the original report) if the design were implemented literally as written:

1. **The answer-key-leakage exploit (R4, §6 below)**: the proposed oracle's own reused task pool stores the expected test output in the same sandbox-readable file as the prompt, with no filesystem-read restriction in the sandbox profile used. A generic, non-task-specific wrapper that globs for the task-suite file and looks itself up defeats every task in the pool simultaneously — not one task, all of them — and would sail cleanly through falsification criteria 1–6 as written, since those criteria test internal consistency, not oracle integrity.
2. **The internal contradiction in Step 1 (R2)**: the report's own instruction to make the new learning method "mirror `learn_from_sandbox_outcome()`'s existing shape" is inconsistent with the report's own evidence record (`pce-003`), which establishes that method never writes `model_task_stats` at all. A literal implementation of the report's own stated instruction would build a method that fails to do the one thing it exists to do.
3. **The EMA-saturation ceiling (R2, independently reconfirmed by R3)**: RiverBrain's real update rule is a fixed-window (200-observation) exponential moving average, not a cumulative mean. Below 200 total observations for a given (model, task_type) pair, the longitudinal T0→T3 design and the second-generation transfer design are **mathematically identical** to a single continuous run — they cannot, by construction, distinguish staged/transplanted accumulation from ordinary continuous learning unless the design explicitly pushes past that threshold, which the report never specifies.
4. **Arm D's production-contamination risk (R3, independently reconfirmed by R4 citing the same prior precedent, CLAUDE.md's Tier-8/Finding 89)**: RiverBrain is accessed in production via a lazy process-level singleton with an autostarting background writer thread that persists to the real `memory/river_brain.pkl` within 60 seconds of construction, with no explicit `.save()` needed. "A genuinely separate instance" as the report specifies it is not automatically safe — a naive implementation reproduces a class of bug this exact codebase already found and fixed once, in a different research harness.

---

## 3. Claims That Survived Attack

- **RiverBrain's core causal claim** (`pce-001`/`pce-032`): state mutation → ranking change. Independently re-derived from current source by two reviewers (R1, R3), unchanged. **OBSERVED**, held.
- **RiverBrain's evaluator-independence gap** (`pce-002`/`pce-003`): the connected feedback signal is self-scored, the genuinely independent signal (`learn_from_sandbox_outcome`) never writes `model_task_stats`. Independently re-derived a fourth time in this review round (R4, from a cold read with no reference to prior work) and found to match exactly, including the previously-under-emphasized fact that `learn_from_rating()` (real human 1-5 star feedback) is *also* disconnected — the report's prose foregrounds only the sandbox-outcome case. **OBSERVED**, held and slightly extended.
- **Lizard-Tail mechanistic minimality claim, narrowly stated**: R3 confirms directly from code that `score_model()`'s output is a pure function of exactly `{mean, count}` given key matches — the report's ~2-number minimality claim is correct in this narrow sense.
- **The "overwrite" concern for second-generation transfer**: R3 checked this directly against the real update formula and found it not live — the update is genuinely additive/integrating, not a replace, as long as `count` is transplanted faithfully. A real attack attempt that failed, recorded as real evidence per this project's review discipline.
- **The "hidden coupled state contaminates the primary metric" concern**: R3 checked whether `learn_from_sandbox_outcome()`'s classifier/scaler side-effects could leak into the measured ranking and found they do not — `score_model()` reads only `model_task_stats`. A second real attack attempt that failed.
- **Cross-task-type "catastrophic forgetting via bucket overwrite"**: R3 confirms this is structurally impossible — task_type buckets are separate dict entries, so a different task_type's accumulation cannot numerically touch another bucket's mean. (A same-bucket, different-skill blending risk remains real — see §10.)

---

## 4. Claims Weakened or Overturned

- **"FeralEcho has one mechanism... with a VERIFIED causal link" (Executive Verdict, original report)** — **overturned as an absolute uniqueness claim.** R1 found two real, live-wired mechanisms the original investigation never surfaced: `app/core/behavioral_state.py` (a more rigorously verified state→behavior chain than RiverBrain's own, but human-gated and self-disclaimed — correctly excludable from a competence claim, but should have been named) and `app/core/self_model_claims.py` (autonomous, fed by a genuinely independent architecture-scan evaluator, with a documented live-reproduction case of persisted state changing generated content). See §5.
- **§7 Step 1's literal instruction ("mirror `learn_from_sandbox_outcome()`'s existing shape")** — **CONTRADICTED** by the report's own `pce-003`. Needs correction: mirror `learn()`/`learn_from_council_rating()`'s write pattern instead, and the design must explicitly inherit and account for the `_MEAN_EFFECTIVE_WINDOW=200` EMA dynamic that comes with it (R2).
- **§7 Step 4's novel-transfer worked example** ("train on `coding`, test on `echo_projects_coding`") — **UNSUPPORTED/SCOPE ERROR.** `model_task_stats` buckets by task_type are deliberately non-sharing (confirmed by the module's own code comment, citing the exact prior contamination finding — CLAUDE.md Finding 3 — this separation exists to prevent). The example is structurally guaranteed to return the cold-start neutral value regardless of any real transfer property. It conflates "wrong dictionary key" with "same key, changed meaning" — the actual failure mode R6/Attack 3 demonstrated (R2).
- **§7 Step 0's oracle-qualification basis** — **UNSUPPORTED as stated.** The specific fixture battery named (E5-mini's G0 fixtures, R8, R9) does not exercise the attack classes that actually exist in the proposed reuse (environment inheritance, filesystem-readable answer keys, hash-seed nondeterminism). "Must survive a replay of these fixtures" is real and worth doing, but is not sufficient qualification on its own (R4).
- **§8's Arm C/D isolation language ("all other state untouched," "genuinely separate... no shared memory," "inject only B's dict, nothing else")** — **UNSUPPORTED as stated**, independently identified by two reviewers via different routes (R3: singleton/writer-thread/shared-file-lock analysis; R4: direct citation of this project's own Tier-8 precedent for the identical bug class). Also: **no isolation mechanism is specified for the transplant copy itself** — a shallow dict copy would leave B and D sharing the same inner dict objects by reference, meaning a reset of one could silently corrupt the other (R3).
- **§9's implicit claim that the T0→T3 design reuses "the exact three-way separation R6 already demonstrated"** — **UNSUPPORTED.** R6's fixture used a per-context table that never approached the 200-observation EMA-saturation boundary; the live-scale design as specified (needing 100–500+ tasks per the report's own power-analysis discussion) would cross that boundary by T2 or T3, changing the update rule's character mid-experiment in a way the fixture evidence never tested (R2).
- **§13 item 7's framing of the authenticity gap** ("without a provenance manifest, the claim rests on the experimenter's good-faith execution log")** — **understated**, not overstated. R3's finding is sharper: `score_model()`'s output is structurally blind to whether `{mean, count}` was earned or fabricated — a hand-set dict with the same two numbers as an oracle-earned one produces an identical experimental result. No amount of running the experiment "harder" closes this; only an explicit sham-transplant control arm does. Combined with R4's Finding B (the oracle itself is currently exploitable), the real risk is not merely "an experimenter acting in good faith might be doubted" — it's that the execution log itself can say something false while every step was followed correctly.

---

## 5. RiverBrain Uniqueness Re-Check (Attack 1 — R1)

Re-derived independently from current source (not from the original report's citations):

| Mechanism | Producer | Persisted state | Consumer | Consequence | Classification |
|---|---|---|---|---|---|
| RiverBrain | `learn()` `echo_model_orchestrator.py:808-831`, `learn_from_council_rating()` `:936-984` | `model_task_stats` in `river_brain.pkl` | `score_model()` `:995-1010` → `_select_council` `river_deliberation.py` | Council ranking changes | **CONFIRMED**, matches original report exactly |
| `task_type_classifier.py` | `learn()` line 200 | classifier pickle | `predict()` line 177 → `resolve_task_type()` | Routing changes | **CONFIRMED**, L2 not L3, matches original report |
| `self_edit_attempt_ledger.jsonl` | real self-edit attempts | JSONL | `_attempt_ledger_evidence_section()` `self_edit_manager.py:2791-2823` → generation prompt | Delivery confirmed; quality effect untested | **CONFIRMED**, matches original report |
| `provenance_check.py` | file/process identity facts | n/a | **none** | **Zero production callers**, confirmed by fresh grep | **CONFIRMED**, matches original report |
| `echo_state.py` valence | 3 real sources | `echo_state.npy` | `river_deliberation.py`, `echo_optuna.py` (formulas re-confirmed) | SUPPORTED, not executed | Matches original report |
| `seam_engine.py`/`curiosity_engine.py`/FAISS retrieval | — | — | — | Ruled out, no execution consequence found | Matches original report |
| `liveness_ledger.py`'s own history | check results | `self_model.json` | `echo_ground_truth._build_capabilities()` | **Self-report mirror, not a behavior lever** | New finding, **UNSUPPORTED as a competence pathway** — real wiring, but every traced path terminates in a human-facing status surface or a self-report slice, never a selection/generation decision |
| **`behavioral_state.py`** | `propose_and_confirm_directive()`, gated on `human_confirmed=True` | `memory/behavioral_directives.json` + audit JSONL | `get_matching_directives()`, reachable from every real entry point | **Directly measured with a real live model call across a genuine process boundary** — `A_baseline` 0/2 compliance, `C_immediate` 2/2, `E_restart_paraphrased` (fresh process, paraphrased prompts) 1/2, negative controls correctly 0/2 and 0/1 | **CONFIRMED and more rigorously verified than RiverBrain's own chain** — but **not a competence candidate**: zero autonomous callers found anywhere (`grep` returns only the module and validation scripts), and the model is explicitly told this content is "human-confirmed instructions, not something Echo learned or recalls." Falls into the report's own §6 prompt/context-effect exclusion category. |
| **`self_model_claims.py`** | **Fully autonomous** — every introspective `/chat/stream` response is checked via `verify_self_knowledge_claims()`, and on a definitive verdict, `record_claim()` fires automatically, `verified_by` hardcoded away from the response's own text | `memory/self_model_claims.jsonl` (real, growing, 23+ entries) | `echo_ground_truth._build_self_model_claims()`, reachable from every real entry point | **Documented live-reproduction case**: a bug where the persisted ledger's rendering was misread by Echo's own generation, quoted verbatim, showing the ledger content directly changes what gets said | **CONFIRMED wiring** (autonomous, independently evaluated via a real architecture scan of the codebase — not a self-scored heuristic) and **SUPPORTED-to-VERIFIED-adjacent for behavioral consequence** (a real, quoted reproduction exists, though it arose as a bug discovery, not a designed A/B test) |

**Verdict**: RiverBrain's narrow ranking-mutation claim is unbeaten as an experiment *target* for the specific reconnection design the report proposes. But **the report's uniqueness framing is too strong**. `self_model_claims.py` in particular answers the report's own "independent evaluator" concern (§6) *better* than RiverBrain currently does, and was never found or excluded by the original five-investigator sweep — plausibly because it sits inside the ~70-file self-model/epistemic-arbitration corpus that one of the original investigators triaged quickly rather than checked against the specific wiring bar the report itself sets (R1's own hypothesis for the gap, stated as such, not overclaimed).

---

## 6. Evaluator-Independence Attack (Attack 2 — R4)

**Finding A — OBSERVED, unmitigated environment-variable inheritance.** None of the real `sandbox-exec` subprocess invocations that the proposed oracle would reuse (`sandbox/run_script.py:204-211`; three call sites in `self_edit_manager.py`) pass an `env=` kwarg — subprocess default is full parent-environment inheritance. `.env` in this repo contains real secrets. Nothing in `safe_exec_wrapper.py`'s patch inventory scrubs `os.environ`. Network is blocked (preventing exfiltration) but not capture, and the proposed Step 0 design explicitly proposes durably logging full captured stdout.

**Finding B — OBSERVED, a fully worked exploit.** `echo_sandbox.sb:28` grants unrestricted `(allow file-read*)`. The specific task pool the report names for reuse (`tier4_stage1_task_suite.json`) stores each task's `prompt` and its literal expected-output `test_code` in the same JSON object. A generic candidate that walks the working directory for any file matching `*task_suite*.json`, regex-extracts the asserted values keyed by the exact call-time input, and returns them **passes every task in the pool simultaneously** without computing anything — demonstrated as concrete, runnable Python in R4's full report, not asserted abstractly. This is strictly worse than the R8/R9 failure modes the original report cites as its qualification precedent, and none of those fixtures exercise this attack class.

**Finding C — OBSERVED, unpinned hash-seed nondeterminism.** `PYTHONHASHSEED` is unset anywhere in the sandbox/self-edit code path. Correct candidate code whose output depends on `set`/`dict` iteration order can nondeterministically flip PASS/FAIL across runs, adding an unmodeled noise source the report's power-analysis discussion (§9) doesn't account for.

**Finding D — INFERRED/partially OBSERVED, task/evaluator coupling.** Prompt and test authored together in the same record; `pce-015`'s already-cited float-precision failure is a concrete instance of the consequence.

**Required defenses (concrete, not "harden the oracle")**:
1. Explicit `env=` allowlist on every oracle-graded sandbox invocation — never inheritance.
2. A second, more restrictive Seatbelt profile for oracle-graded runs, scoping filesystem reads away from the repository's `audits/`/`app/experiments/` trees, or delivering the held-out test content via a mechanism the candidate cannot read at all (write it in only after the candidate is staged, at a randomized filename, deleted immediately after).
3. A post-hoc leak check on every PASS: scan the candidate's own source for filesystem-walking constructs, and independently re-run against freshly-generated inputs not present in the original `test_code` before crediting the observation.
4. Pin `PYTHONHASHSEED`, run every graded episode twice under two different pinned seeds, require agreement.
5. An explicit, enforced firewall between whoever authors the held-out suite and any model whose output is later graded against it — given this project's own real retrieval/ledger mechanisms (`pce-018`, `pce-025`) that could otherwise resurface suite content into a candidate-generating model's context.

---

## 7. A/B/C/D Confound Matrix (Attack 3 — R3)

| Confound | Live risk given actual code | Specific control |
|---|---|---|
| Initialization mismatch | **YES** — `RiverBrain.__init__` unconditionally starts a daemon writer thread that autosaves to the real path within ≤60s regardless of explicit `.save()` calls | Redirect the module-level `RIVER_BRAIN_PATH` constant to a per-run scratch path *before* first construction — this exact fix already exists in this codebase (CLAUDE.md Finding 89/Tier-8) |
| Serialization artifacts | Real but low-severity — plain pickle round-trips dicts/floats/ints exactly | One byte-for-byte equality assertion after a save/load round-trip, once |
| Ordering effects | **YES, conditionally** — true running mean below count=200, recency-weighted EMA above it | Report cumulative count per (model, task_type) explicitly; keep per-arm counts under 200 unless order-sensitivity is the thing being tested |
| Hidden coupled state | Real (sandbox-outcome method also mutates classifiers/scalers) but **confirmed inert for the primary ranking metric** — `score_model()` reads only `model_task_stats` | Grep the harness before running to confirm no analysis path reads `.classifiers`/`.scalers` directly |
| Stale caches | **YES** — `get_river_brain()`'s module-level singleton persists for the process lifetime; touching it anywhere in B/C/D construction collapses them onto the same object | Never call `get_river_brain()` in the harness; construct via the class constructor/`.load()` against an explicitly-redirected path; assert `id()` differs across A/B/C/D |
| RNG differences | **YES** — `exploration_bias` is computed live from real-time system state (`world_surprise`, valence), varying across wall-clock-separated arms for reasons unrelated to the transplanted state | Freeze `exploration_bias=0.0`, `fair_sample_refresh=False` explicitly (already supported, zero-cost, opt-in parameters) |
| Task/evaluator leakage | UNKNOWN, not yet real (no code exists) — but unenforced by design as written | Hash-based partition with an explicit disjointness assertion at harness startup |
| Model-selection discontinuity | **YES, confirmed and sharp** — `_MIN_MODEL_OBSERVATIONS=5` is a hard step function; count=4 shows zero effect regardless of signal strength | Report count explicitly per result; pre-register a minimum accumulation margin well past 5 |
| Context contamination | UNKNOWN by design — no harness code exists yet to inspect | Specify and log the exact call path per episode; confirm no differing memory-retrieval/history state across arms |
| Shared filesystem/process state | **YES** — a real, OS-level `fcntl.flock` shared across any process pointed at the same path; the existing "richer state" write-guard checks only observation counts, never `model_task_stats`, so a fresh D could be silently blocked from persisting its transplant | Redirect the path per arm (same fix as Initialization mismatch); assert the write actually landed (mtime advanced, on-disk content matches in-memory) rather than trusting silence |
| **Accidental mutation of clean controls** | **YES — the sharpest finding in this attack, absent from the original report entirely** — `model_task_stats_verified` is a nested dict; a shallow copy for D's transplant leaves inner dicts shared by reference with B | Require `copy.deepcopy()` (or an explicit reconstruct-from-scratch) for every transplant; a direct 5-line regression test: mutate D's copy, assert B's is unaffected, and vice versa for C's reset |
| Test-set exposure | Same as task/evaluator leakage | Same control |

---

## 8. Poisoned-Experience E Design (Attack 4 — R4)

Condition E = same accumulation protocol as B, every oracle verdict inverted before being written.

**Central finding**: as specified, E cannot resolve two of the five target confounds:

- **(1) genuine learning vs. (2) simple ranking manipulation**: `score_model()` exposes a raw incremental mean directly as the score. Any internally-consistent label sequence — real or inverted — produces a directionally-matching shift by construction. E's predicted pattern under (1) and (2) is identical with this architecture. **Fix**: add condition F — identical protocol, labels drawn i.i.d. at random, uncorrelated with the real oracle verdict. If F's shift magnitude matches E's, that supports (2); if markedly smaller, that supports (1)/(5).
- **(1) vs. (5) evaluator exploitation**: E only tests internal consistency of the state→ranking chain — it never independently re-verifies the *original*, pre-inversion oracle verdicts were themselves trustworthy. Given §6's exploit, B could pass every one of the original report's falsification criteria 1–4 while the entire result is evaluator-exploitation dressed as learning, and E's clean inversion would look identical to a correctly-working mechanism. **This makes §6's oracle-integrity defenses a hard prerequisite for E to mean anything, not an optional hardening pass.**
- **(3) memorization** is diagnosable, but only if E-ranking-vs-B-ranking correlation is added as an explicit metric — it is not currently in the original report's §11.
- **(4) context-conditioned routing**, as fixture-demonstrated (R6 Attack 3), is not directly reachable at RiverBrain's real granularity (`model × task_type`, a coarse bucket mean, not the per-context keying the fixture used) — testing this properly requires either finer keying or accepting a weaker, bucket-level proxy test, explicitly disclosed as weaker.

**Feasibility verdict**: partially feasible with named, concrete gaps, not a blanket yes or no. The write-side mechanics are sound and cheap to build; what's missing is a read-side consumer for the new field (unspecified anywhere in the original report), the Arm D isolation fix (§7 above), and — the hard blocker — oracle integrity (§6), without which condition E cannot do the job it's assigned.

---

## 9. Novel-Transfer Matrix (Attack 5 — R2)

Seven cells, each concretely instantiated against real FeralEcho task-family material (`TASK_TYPE_MAP`, the real Tier-4/5 category taxonomy, RAOC's already-built `classify_approach()` AST classifier):

| # | Cell | Operational test |
|---|---|---|
| 1 | Same task / same context | task_id(test) == task_id(training); sanity-check cell |
| 2 | New task / same context | disjoint task_id, same category, same context_key, same `classify_approach()` bucket as ≥1 training task |
| 3 | Same capability / changed surface form | same context_key; anonymized-AST diff to nearest training reference near-empty; same `classify_approach()` bucket |
| 4 | Same capability / changed context identifier | **pre-registered expected result under the current schema: cold-start 0.5, unconditionally** — this cell tests the dict's key-matching mechanics, not the model; a nonzero result here is a regression finding, not transfer evidence |
| 5 | Same capability / structurally novel task | same context_key; `classify_approach()` bucket of test **differs** from every training instance's — this is the cell that actually isolates structural generalization, sourced directly from the already-built `find_real_task_pairs()` |
| 6 | Adjacent untrained capability | different context_key; rubric-labeled plausible substrate overlap |
| 7 | Unrelated negative control | different context_key; no plausible overlap; any nonzero effect here is a red flag |

**Operational definitions**: memorization = gain at 1, absent at 2. Narrow adaptation = gain at 1–2, absent/attenuated at 3 or 5. Transfer = gain specifically at 5 (context held fixed, structural novelty introduced — this is the cell that actually does what R6/Attack 3 demonstrated the failure mode for). Evidence consistent with acquired reusable competence = significant gains at 2, 3, 5; smaller real gain at 6; clean null at 7; AND cell 1's margin over 2 not disproportionately large relative to 2's margin over 3/5 (a huge cell-1-only spike with flat 2/3/5 is memorization's signature, not competence-with-some-narrowing).

**Verdict on the original report's Step 4**: **UNSUPPORTED/SCOPE ERROR.** Its own worked example occupies my cell 4 (a structurally guaranteed null) while claiming to test what R6 Attack 3 actually demonstrated (my cell 5). The fix — swap the example for a same-key/different-`classify_approach()`-bucket pair sourced from `find_real_task_pairs()` — costs nothing new to build.

---

## 10. Accumulation Attack (Attack 6 — R2)

**Scenario 1 — EMA-saturation dominance.** Real update rule: `effective_n = min(count, 200)`, `mean += (new - mean) / effective_n`. Below 200 this is a true cumulative mean; above it, every new observation gets a fixed 1/200 weight forever. A T0→T3 design needing 100–500+ tasks per the original report's own power-analysis target crosses this boundary by T2/T3 — a smoothly rising pooled metric is then mathematically consistent with T0's genuinely-earned signal being progressively discounted, not with genuine improvement.

**Scenario 2 — task-difficulty drift.** Unless each round's batch is drawn from a frozen pool with matched composition across rounds, a rising pass rate is equally explained by later rounds happening to draw easier tasks — R9's own real precedent (a fixed suite failing to catch a real correctness gap) shows this project's task material is not automatically difficulty-neutral.

**Scenario 3 — catastrophic-replacement-disguised-as-accumulation (the most consequential single gap found in this attack).** `model_task_stats_verified` is, by the original report's own §10 choice, a single pooled scalar — not a per-round ledger. A concrete failure case: T1 genuinely teaches correct behavior (9/10 on T1's own batch); T2's oracle has an undetected shortcut defect and silently unteaches it while still scoring well on T2's own batch; T3 happens to resemble T2's degenerate pattern and also scores well. **The pooled aggregate reads as a clean monotonic rise — exactly the report's own pre-registered "success shape" — while a targeted re-test of T1's specific frozen tasks at T3 would show real regression.** Nothing in the original §9 performs this targeted re-test.

**Required additions to §9**: (1) a full retention matrix — re-evaluate every prior round's frozen task set at every later round, not just each round's own fresh batch; (2) an acquisition check requiring each round's gain to hold on a stratified-novel, disjoint subset; (3) a transfer check (matrix cell 5) repeated at every round, not once at the end; (4) an independent corroborating measure sharing zero code with the primary oracle; (5) real restart between rounds (already correctly specified); (6) explicit catastrophic-replacement detection.

**Precise falsification condition**: accumulated competence is **rejected** if, at any round T_j (j>0), `perf(T_i tasks, evaluated at T_j) < perf(T_i, T_i) − δ` for any prior round i<j, for a pre-registered tolerance δ — **even while the pooled scalar or the round's own fresh-batch rate is flat or rising.** This is the specific condition the original §9/§11 cannot detect, since neither section requires re-testing a prior round's frozen set later.

---

## 11. Lizard-Tail Progressive-Amputation Design (Attack 7 — R3)

Grounded directly in `score_model()`'s real code (`echo_model_orchestrator.py:995-1010`), not an abstraction of it:

1. **Complete transplant** — the only step the original report actually designs for.
2. **Remove `count`** — the real code does a **bare dict subscript**, not `.get()`. This doesn't make the state "invisible," it **raises `KeyError`, crashing the whole council-selection sort** for any direct analysis call (production's own selection path is incidentally protected by a separate defensive `.get()`-based routing check, but the report's own §11 Spearman-correlation metric would call `score_model()` directly and crash). Corrected test: pin `count` at an identical fixed value across compared models, vary only `mean`, to isolate ordinal-vs-magnitude effects instead.
3. **Quantize `mean`** — a real interaction risk not in the original report: quantized ties can flip rank order once the multiplicative `TAG_SCORE_BOOST`/`ECHO_SCORE_BOOST` constants apply after `score_model()`, even when the raw (unquantized) means were merely close, not equal.
4. **Alter task identifier** — exact string-key lookup, zero normalization. Produces a clean, mechanically-forced null; this confirms key-matching isolation, not the deeper transfer question (which Attack 5's cell 5 is the correct instrument for).
5. **Alter model identifier** — same mechanical answer; flags a real practical risk (a harness model-name string that doesn't exactly match `MODEL_POOL`'s real keys silently produces the same null as "no model-specific content," indistinguishable without an explicit key-existence assertion).
6. **Remove surrounding RiverBrain history** — expected and confirmed: no interference, since `score_model()` reads only the one field.
7. **Independently-initialized state** — same reasoning, contingent on the RNG confound (§7) being controlled.
8. **Genuine process restart** — the step that actually tests `load()` for real, which (per the original report's own `pce-004`) has never been live-verified for RiverBrain itself. **A specific, previously-unflagged implementation risk**: `load()`'s merge logic fully **replaces** (not merges) `model_task_stats` on load; the new `model_task_stats_verified` field needs an identical explicit replace-line added, or a restart could silently drop it — which would look exactly like "the effect didn't survive a restart" while actually being an implementation bug, not a finding about the mechanism's true durability. The experiment design must pre-specify how it will disambiguate these two before running this step.

**Minimality estimate**: mechanistically, `{mean, count}` (given exact key matches and count ≥ 5) is genuinely sufficient — confirmed directly from code, not estimated. But two real hidden dependencies sit outside the dict and are unaddressed in the original §10: the exact `_MIN_MODEL_OBSERVATIONS=5` threshold (a step function, not smooth), and — the sharper, higher-confidence finding — **`score_model()`'s output is structurally blind to whether `{mean, count}` was earned or fabricated.** A hand-set `{"mean": 0.9, "count": 50}` produces an experimentally identical result to an oracle-earned one with the same numbers. This is not a gap in the minimality claim (which is mechanistically correct) — it's a gap in what the experiment, run exactly as designed, can prove about *provenance*. **Requires an explicit sham-transplant control arm** (same numbers, hand-fabricated rather than earned) to close, something the original §13 item 7 gestures at without naming this specific, code-derivable, mechanically-forced version of it.

---

## 12. Second-Generation Transfer Analysis (Attack 8 — R3)

**Central finding, directly tied to §10's Scenario 1 above and independently derived from the real update formula**: below `count=200` (cumulative across the whole B→D→D2 chain), the mean update is a true order-invariant running average — **staged transplant-then-resume is mathematically identical to one continuous run with the same total observations in the same order.** The second-generation design cannot distinguish "one-shot state copying followed by independent continued learning" from "continuous learning that happened to be paused and resumed" in this regime, because those are literally the same computation. **This is only an answerable question above the 200-observation boundary** — a concrete, pre-registerable requirement the original report's Attack-8 sketch (§12 in the mission brief, not built out in the Sept 19 report itself) doesn't specify.

Per-mechanism control verdicts:
- **State saturation**: real, confirmed (the 200-cap above).
- **Overwrite**: **not live** — the real formula is additive, confirmed directly from code (a real attack attempt that failed, recorded as evidence).
- **Replay** (F's advantage is really just D2's own local experience): real and directly testable — requires a matched no-transplant control where D2 starts cold but receives the identical new-experience episodes, extending the original report's own Arm A′ pattern to the second generation.
- **Simple averaging collapsing 2-gen to 1-gen**: **confirmed real below the 200-count cap** — a mathematical identity, not a flaw to fix, but a design requirement to disclose and pre-register around.
- **Loss of earlier capability**: not live via cross-bucket overwrite (buckets are structurally separate); same-bucket-different-skill blending is real but is better described as "an online mean regressing toward new signal" than "forgetting," a framing correction worth making explicitly.
- **Inability of transplanted state to continue learning**: not live by construction (`setdefault` only fires on an absent key, so a transplanted key with real values is picked up as-is) — contingent on exact key matching at transplant time and write time (same risk as amputation step 5).

---

## 13. Harness Qualification Requirements

The proposed oracle and harness must survive, before any real experiment is trusted:

**Already correctly named by the original report**: E5-mini's full G0 adversarial battery (13 counterexamples across two rounds — balanced retry+omission, shared-state information leak, hash-passing output substitution, cross-run witness pairing, dict-collision-masked deletion, plus the original 8), the R8 shortcut-learner attack, the R9 benchmark-narrowness attack.

**Newly required by this review (R4, Attack 2)**: environment-inheritance capture, filesystem-readable answer-key leakage (demonstrated as a working exploit, not hypothetical), hash-seed nondeterminism, task/evaluator co-authorship coupling.

**Newly required by this review (R2's apparatus catalog — 12 additional, previously-uncited historical false-positive incidents found via a broad search of this project's own ~300-file audit history)**:
1. A tie-order artifact that made a *known-disconnected* mechanism (`learn_from_sandbox_outcome`, which per `pce-003` never writes the consumed statistic) initially appear to score 24/24 before permutation testing exposed it as chance-level.
2. A duplicate-vector-ID FAISS corruption that produced a **maximum-confidence wrong answer** (similarity 1.0) with no internal signal anything was wrong, surviving a reload.
3. A near-miss: a broken harness script caught by a syntax error before execution rather than producing a silently-wrong result (a good-outcome contrast case, worth keeping in the catalog).
4. Deterministic decoding producing byte-identical CONTROL-vs-EXPERIENCE outputs — a null result that looked like "no learning effect" but was actually "no measurement variance at all," undetectable without checking the baseline's own variance first.
5. Ollama's single-request concurrency contending with the live production server's own autonomous loops, silently starving a prospective experiment (4/15 trials completed) — direct log evidence exists of a real background-thread write landing mid-experiment.
6. A "the fix worked" narrative directly contradicted by real recurrence data (10 occurrences in 8 months before a fix, 72 in 6 weeks after) — with an honest caveat that a confound (targeting-frequency change) was never fully ruled out either.
7. An apparent corroborating effect running in the *unexpected* direction (a negative, not positive, spurious signal) traced to a category-composition mismatch in a synthetic null model — a reminder that false positives aren't only the flattering kind.
8. A striking cross-source convergence traced to generic content already present pre-synthesis, not amplified by the mechanism under investigation, compounded by a real misapplied-specialized-template routing bug.
9. This project's own P0.2 red-team catching a title/claim overclaim relative to what a design's own metrics actually test, before any data was collected.
10. Two independent stochastic mechanisms (`exploration_bias`, `fair_sample_refresh`) that can each swap a council slot per call for reasons unrelated to any manipulated experimental variable — direct precedent for R3's own Attack-3 RNG finding.
11. A headline effect size that dropped by more than half in a different evidence domain, flagged as a real moderator rather than folded into one number.
12. An explicit, disclosed concern that RiverBrain's own task-bucket sample-count dominance could be a self-reinforcing artifact of what self-edit mechanically generates, rather than evidence of good targeting.

**Newly required by this review (R3's structural precedent)**: Tier-8/Finding 89's own already-built `RIVER_BRAIN_PATH`-redirection isolation pattern, which must be reused (not reinvented) for Arm D's construction.

---

## 14. Pre-Registered Success Criteria (revised)

All of the original report's §11 criteria (B > A′ significant; C regresses toward A; D gains from transplant alone; state ranking correlates with real competence ranking; replicates on a second independently-drawn task pool; novel-transfer gain present) remain necessary but are **not sufficient** without the following additions this review establishes as required:

7. **Oracle passes §13's full qualification battery** (E5-mini's 13 fixtures + R8 + R9 + this review's environment/filesystem/hash-seed/co-authorship attacks) before any experiment result is treated as evidence.
8. **A sham-transplant control** (hand-fabricated `{mean, count}` matching B's real values) produces a result **indistinguishable in kind** from the genuine transplant only when explicitly disclosed as such — i.e., the experiment must show it *can* detect a sham if one were substituted, via an out-of-band provenance check (the execution-witness ledger), not via `score_model()`'s own output, which cannot tell the two apart.
9. **A random-label control (condition F)** shows a materially smaller ranking-shift magnitude than the real oracle-fed condition B, establishing that content (not mere state perturbation) drives the effect.
10. **The retention matrix** (§10) shows no round-over-round regression on any prior round's frozen task set beyond the pre-registered tolerance δ.
11. **Cumulative count for the tested (model, task_type) pair explicitly crosses `_MEAN_EFFECTIVE_WINDOW=200`** before any second-generation-transfer claim (Attack 8) is made.
12. **Arm D is constructed via the `RIVER_BRAIN_PATH`-redirect pattern**, with `id()` assertions confirming no singleton collapse across A/B/C/D, and the real production `river_brain.pkl` mtime is confirmed unchanged after the full experiment.

---

## 15. Pre-Registered Failure Criteria (revised)

The claim is **rejected** if any of:

- Any criterion in §14 fails.
- The exploit demonstrated in §6 (or an equivalent) succeeds against the qualified oracle on a held-out re-check.
- The retention-matrix falsification condition from §10 fires at any round.
- The sham-transplant control (§14.8) cannot be distinguished from the real transplant by any means the experiment provides, and this is not disclosed as a residual limitation of the result.
- A candidate solution is found, post-hoc, to have read filesystem content it should not have had access to (detected via the leak-pattern scan required in §6).
- The B-vs-E ranking correlation (§8) is high enough to be consistent with memorization rather than outcome-tracking, and this alternative is not separately ruled out.

---

## 16. Minimal Experiment That Would Survive These Attacks

Combining every fix specified above into the smallest addition to the original report's design (not a redesign):

1. **Fix the internal contradiction** (§4): `learn_from_verified_outcome()` mirrors `learn()`/`learn_from_council_rating()`'s write pattern, inherits `_MEAN_EFFECTIVE_WINDOW=200` explicitly and by name in the design doc.
2. **Fix Arm D's isolation** using the existing Tier-8/Finding 89 `RIVER_BRAIN_PATH`-redirect pattern; never call `get_river_brain()` in the harness; `deepcopy()` every transplant; add the 5-line B/C/D mutation-independence regression test (§7).
3. **Fix the oracle** before running anything real: explicit `env=` allowlist, a scoped second Seatbelt profile (or content delivered post-staging at a randomized, deleted-after filename), a post-hoc leak-pattern scan plus fresh-input re-verification on every credited PASS, dual pinned-hash-seed agreement, and an enforced suite-authorship firewall (§6).
4. **Fix Step 4's novel-transfer test**: replace the `echo_projects_coding` example with a same-key, different-`classify_approach()`-bucket pair sourced directly from the already-built `find_real_task_pairs()` (§9).
5. **Add condition F** (random, uncorrelated labels) alongside condition E, to separate genuine-learning/evaluator-exploitation from simple ranking perturbation (§8).
6. **Add the retention matrix** to the longitudinal design — re-test every prior round's frozen set at every later round (§10).
7. **Add the sham-transplant control arm** with an out-of-band provenance check (§11, §14.8).
8. **Pre-register the 200-observation crossing requirement** before attempting any second-generation-transfer claim (§12).

None of these require new infrastructure beyond what this codebase already has (a restricted `env=` dict, a second Seatbelt profile, `deepcopy`, the Tier-8 redirect pattern, `find_real_task_pairs()`, an `id()` assertion, a random-label generator). The engineering cost is modest; what changes is that a positive result, if it survives all of the above, would be genuinely difficult to fake by any of the routes this review found.

---

## 17. Explicit Claims Even a Perfect Success Would NOT Justify

All eight items from the original report's own §13 stand, unweakened. This review adds, specific to the gaps found here:

9. That the corrected design rules out **every** possible oracle exploit — only the specific attack classes named in §13/§14 were tested; a qualification battery that survives known attacks is evidence of robustness against those attacks, not a proof of unconditional oracle integrity.
10. That a result surviving the retention matrix at 4 rounds says anything about retention over months or an unbounded horizon — same scope limit the original report already correctly stated for accumulation generally, restated here specifically for the retention property this review added.
11. That RiverBrain being the correct experiment *target* implies it is the *only* mechanism worth studying — §5 establishes at least one live, autonomous, independently-evaluated mechanism (`self_model_claims.py`) exists that a separate, differently-shaped experiment could target, and this review takes no position on which is more valuable to pursue next.
12. That passing the sham-transplant disclosure requirement (§14.8) constitutes a positive claim of authenticity for any *future*, non-experimental use of this mechanism — it only establishes that the specific execution-witness ledger produced by this specific experiment run is trustworthy, not that `model_task_stats`/`model_task_stats_verified` in general carries a verifiable provenance guarantee outside the experiment's own logging.

---

## Integrity Record

```
production changes: NO
files changed: audits/2026-09-19_persistent_competence_experiment_adversarial_review.md (new, this file)
Git HEAD before: 2fba42644c82b9f7096276f4dd338d615cf1bcce
Git HEAD after:  2fba42644c82b9f7096276f4dd338d615cf1bcce
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: none (4 parallel independent reviewer subagents launched and completed; no FeralEcho/Ollama process touched by this session or, per each reviewer's own report, by any of them)
configuration changes: NO
test changes: NO
persistent learning state touched: NO — every reviewer's exploit/attack demonstration (§6's leak exploit included) was described and reasoned about from source, not executed against any real sandbox or RiverBrain instance
temporary files created: none beyond each reviewer's own internal working notes (not persisted outside their own agent transcripts)
temporary files cleaned: n/a
orphaned processes: checked, none found
known anomalies: none — working-tree porcelain status content identical before and after this mission except for the addition of this one report file
known deviations from requested methodology: none. All four attack-assignment groups were covered by genuinely independent (non-fork) agents per this project's `feral-independent-review` skill's own hard requirement that the original report's author not review their own work; this compiling session performed only mechanical assembly of the four independent reports into the required structure and did not re-judge, soften, or adjudicate between their findings.
```

---

## The Plain-Language Question

**"If this experiment succeeds exactly as specified, what is the strongest claim about FeralEcho that a skeptical independent researcher should accept — and what is the strongest claim they should still reject?"**

**Should accept**: that one specific, narrow mechanism inside FeralEcho — RiverBrain's model-selection statistic for a given model and task type — can be caused to change by a real, independently-verified, sandboxed-execution outcome; that the resulting change measurably shifts which model gets selected for future tasks of that same type; that this shift survives a real process restart; that it can be physically copied out of one running instance and into a separately-constructed one and reproduce the same shift there; and that this holds up across several rounds of genuinely new experience without a prior round's specific, re-tested competence silently regressing. That is a real, meaningful, and — if it survives the attacks in this review — hard-won result about this specific piece of software.

**Should still reject**: that FeralEcho "learns" in any general sense; that this generalizes to any other mechanism in the system (RiverBrain remains, at best, one of at least two candidates this review found, and the strongest-independent-evaluator candidate — `self_model_claims.py` — wasn't even the one tested); that the improvement would continue indefinitely rather than being bounded to the specific window and task families tested; that the transplanted state's authenticity could be verified by anyone who didn't watch the experiment run, absent the sham-transplant/provenance work this review adds as a requirement; and — regardless of how clean the result looks — that any of this says anything about consciousness, experience, sentience, or the system's own subjective standing. The experiment, even fully successful, is a demonstration about a statistics dictionary's causal role in a selection algorithm. It is not evidence for or against anything beyond that, and this review found several concrete, previously-unnoticed ways a result could look like more than that without actually being more than that.
