# Pre-Registered Minimal Persistent-Routing-Learning Experiment — Design

Read-only. Git HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce` unchanged before and after (confirmed by direct `git rev-parse` before and after this synthesis). Nothing was implemented, run, or modified. This document designs a protocol; it does not execute one.

**Sources reconciled**: `audits/2026-09-22_claude_reconciliation_of_codex_learning_attack.md` (this session), `audits/2026-09-22_codex_adversarial_attack_on_reconciled_roadmap.md`, `audits/2026-09-22_task_correctness_evaluator_qualification.md` (this session), `audits/2026-09-22_self_edit_candidate_logging_implementation.md`, and direct re-reads of `app/core/river_deliberation.py`, `app/core/task_type_classifier.py`, `app/core/council_rater.py`, `app/experiments/accumulation_probe/*` performed in this session specifically to ground this design rather than trust prior prose. Neither my own nor Codex's prior conclusions were assumed correct without a source check; where a prior claim could not be re-verified in the time available, it is marked UNKNOWN rather than inherited as fact.

## 1. Executive verdict

A minimal, interpretable protocol can be specified now, without inventing new grading or task-construction infrastructure — AP-0's existing stack (`worlds.py`/`tasks_v2.py`/`make_cases2()`/`jail.py`/`freeze.py`/`oracle_b_v2.py`) and `oracle_runner.grade()` (per the evaluator-qualification report) supply everything needed for the task substrate and correctness measurement. **The design deliberately does not reuse Echo's live conversational/self-edit machinery (RiverBrain, the attempt ledger, council rating, the task-type classifier) at all** — not because those are broken, but because entangling them would reopen every experience-channel-freezing problem Codex's attack raised, for no scientific benefit: the bounded claim under test is about a *dedicated, standalone selector* over a *fixed strategy menu*, not about whether Echo's production pipeline is currently learning. This is a smaller, cleaner substrate than "make production Echo learn," and it is what makes freezing every other channel (§7/§10) tractable rather than aspirational. Two pieces of real, non-trivial new engineering are required and do not exist anywhere in this repository today: a replay-from-checkpoint mechanism for the experience-substitution intervention (§9), and a genuine multi-process restart-boundary harness (§11). Both are specified precisely enough to build, neither is exotic, and neither has been attempted. Implementation remains **NOT AUTHORIZED** — this document is the frozen protocol to be adversarially reviewed next, not a green light.

## 2. Exact bounded claim

**The claim this experiment could establish, stated exactly:**

> In a standalone, isolated selector choosing among a fixed menu of problem-solving strategies for a fixed family of hidden-test-graded coding tasks, a policy that is permitted to update from independently evaluated (PASS/FAIL) outcomes of its own past decisions achieves a higher holdout PASS rate on structurally-related-but-non-identical task instances than both (a) a competent, development-selected, non-updating contextual router and (b) an architecturally identical twin whose updating is disabled after the same development phase — and this advantage survives a genuine process restart, and is shown, via direct state substitution, to be caused by the retained state rather than by incidental confounds.

**What it could NOT establish, stated before any machinery is designed, per the mission's own instruction:**

- General intelligence, general learning, or any claim about Echo's cognitive capacities as a whole.
- Recursive self-improvement, open-ended learning, or accumulated competence across repeated experimental rounds (this is one rung, not a ladder-climbing demonstration).
- Anything about live, production Echo's actual self-edit pipeline, conversational behavior, or RiverBrain — the experimental selector is a new, dedicated artifact, not a stand-in for any production mechanism, and a positive result here says nothing about whether production Echo is or isn't doing anything like this today (per the reconciliation report, it demonstrably is not, in the one indirect path Codex found).
- Autonomous scientific discovery, singularity-adjacent claims, or anything about consciousness, valence, or experience in the phenomenal sense.
- Generalization *beyond* the fixed strategy menu and fixed feature space defined in §6/§9 — the selector cannot propose a new strategy or expand its own representation; success here says nothing about whether it could (§23).
- A claim that the *underlying model's* raw coding capability improved — every strategy's ceiling is fixed by the same frozen model/digest across all arms; only *routing among existing strategies* is under test.
- Any claim from a single replicate lineage — see §4/§18 on why a single history is not statistically independent evidence.

## 3. Experimental unit

**The correct independent unit for statistical inference is the replicate lineage (development → prospective-accumulation → holdout), not the individual holdout task.** Reasoning, worked through rather than assumed: within one lineage, every holdout-phase decision made by the adaptive arm (Arm C) is conditioned on the *same* persisted selector state, `S1`, which was itself shaped by the *same* sequence of prospective experiences. Holdout task outcomes within a lineage are therefore correlated through that shared state — a systematic bias in `S1` (good or bad) will push every holdout decision in the same direction, which is exactly the kind of non-independence a plain per-task binomial test would silently ignore, producing overconfident significance from what is really a sample of one. This mirrors a cluster-randomized design: **lineage = cluster, holdout task instance = observation within cluster.** Multiple independent replicate lineages (distinct random-seed families, each running its own full development→prospective→holdout cycle) are the actual unit that earns statistical power; a single lineage, however many holdout tasks it contains, is one data point for the primary between-arm comparison. Task, experience, update, and policy-history are all real, named entities in the causal chain (§8) but none of them is the correct *unit of independence* — only the lineage is.

## 4. Task substrate

AP-0's existing infrastructure is sufficient, reused as follows, none of it invented for this mission:

- **`worlds.py`**: supplies fresh, non-dictionary pseudo-word "convention realizations" per seed — draws a genuinely novel surface vocabulary the frozen model has not seen in training, which is the actual mechanism closing the memorization confound (not a nonce, not a nonce-marker — the *content* itself is unseen). A fresh, disjoint seed range (never used by AP-0's own dev/qual missions — confirmed via `qual.py`'s own `MASTER_SEED + 7000 + ...` offset convention that such disjoint ranges are the established practice, not a new idea) must be drawn specifically for this experiment.
- **`tasks_v2.py`'s T/S/NEAR/UNREL split**, mapped to this experiment's claims ladder precisely:
  - **T** (base template, same convention kind the prospective phase trained on): fresh instances (never-seen exact input tuples) of the *same* template family used during prospective accumulation. Success here supports only **repetition-level evidence** — the selector has seen this exact template/strategy pairing rewarded before; it is the weakest positive result and must not be reported as transfer.
  - **S** (surface-variant: same underlying skill, different input shape — tuples instead of dicts, a parsed string instead of structured records): a genuinely different surface form of the same logic. Success here beyond both controls is the experiment's **primary claim-bearing evidence** — narrow structural transfer.
  - **NEAR** (a plausible-but-different task sharing vocabulary and surface shape, where the *correct* strategy is not the one favored by the trained convention): this is a **specificity control, not a transfer-credit opportunity** — pre-registered here, explicitly, before any data exists: a well-calibrated, genuinely feature-conditioned selector should *not* show an unwarranted advantage on NEAR from blindly favoring the strategy that won on T/S; if it does, that is evidence of overgeneralized routing, not learning, and must be reported as a negative finding, not folded into the transfer claim.
  - **UNREL** (unrelated control): a positive delta here is a **red flag requiring investigation** — evidence of a confound (general warm-up effect, prompt-formatting artifact, non-specific score drift), never evidence for the hypothesis. Pre-registered as such before any run.
- **`make_cases2()`**: mutant-killing hidden test construction with equivalence-checking on 4,000 extra random inputs — reused verbatim as the hidden-test generator for every task instance in every split.
- **`jail.py`**: OS-level Seatbelt confinement, reused with a *new* profile scoped to this experiment's own root — see §21 and §16.
- **`freeze.py`**: the hash-and-assert pattern, reused verbatim, extended to cover this experiment's own new code and new frozen artifacts (strategy menu, selector architecture, DEV/PROSPECTIVE/HOLDOUT task files) before any real generation call.
- **`oracle_b_v2.py`**: the independent-second-implementation pattern for catching oracle bugs — reused as a template; a second, differently-idiomed reference solution must exist for whatever task templates this experiment defines, mirroring this exact precedent.

**No post-hoc task-family selection**: DEV, PROSPECTIVE, and HOLDOUT partitions are drawn from disjoint seed ranges and frozen (hashed, `write_json_new`'s refuse-to-overwrite semantics) before any real generation call for any arm. The HOLDOUT partition is not read, inspected, or referenced by any researcher or any piece of harness code until the primary analysis begins — mirroring `freeze.py`'s existing `chmod 0o444` post-freeze read-only convention, extended to mean "not opened at all," not merely "not writable."

## 5. Hidden evaluator contract

**`oracle_runner.grade(candidate_code, test_code) → {"passed": bool, "ran_ok": bool, "output_tail": str, "error_tail": str, "infra": bool, "timeout": bool, "duration": float}`**, called only by the harness controller process (never inside a generation arm's own jailed subprocess), with a fresh `secrets.token_hex(8)` nonce per call — reused exactly as it exists today, no modification. `test_code` is built once per task instance by `make_cases2()` at task-freeze time, never regenerated per call. Ground truth for each task instance is the primary reference solution plus the independent second implementation (`oracle_b_v2.py`-style) cross-check, run once at freeze time to catch oracle bugs before any real model call — mirroring AP-0's own `oracle_qualification` report step referenced in `freeze.py`'s `collect()`.

## 6. Sanitized feedback contract

**The learner (the selector's `update()` call) receives exactly one tuple per completed decision: `(task_feature_signature, strategy_used, outcome ∈ {PASS, FAIL})`.** Nothing else. Specifically excluded from ever reaching `update()` or any file the selector reads: `output_tail`, `error_tail`, `duration`, the raw `test_code`, the raw candidate code, and any expected value. **PASS/FAIL alone is judged sufficient and is the pre-registered choice** — no richer feedback bit is included, for two reasons stated explicitly rather than defaulted into: (1) the bounded claim under test is about *routing* improvement, not *diagnosis-driven repair* — a richer failure-class signal would test a different, larger, already-partially-explored claim (Architecture A's own null result, per the reconciliation report §7, is specifically about diagnosis-injection, and this design deliberately avoids re-running that same intervention under a new name); (2) every additional bit widens the surface for the evaluator-qualification report's own named leakage risk (`output_tail`/`error_tail` can echo assertion-comparison fragments) — the smallest sufficient channel is the one that cannot leak by construction, because it never carries the leakable fields at all. `task_feature_signature` is derived only from information available at generation time (the task's rendered prompt text — function name, argument names, natural-language spec), computed by a fixed, frozen feature extractor (§9) — never from the T/S/NEAR/UNREL split label itself, which is researcher/experimental bookkeeping the selector must not have access to (using the split label as a feature would make the "specificity control" in §4 meaningless by definition).

## 7. Experimental arms

All three are necessary, and the reasoning for each is a distinct question, not redundant rigor:

- **Arm A — frozen contextual champion.** Answers: "how good is the *best static engineering* a competent human, working only from development data, could build?" Necessary because a persistent-learning claim is meaningless unless it is compared against the ceiling a non-learning system could plausibly reach — this is Codex's central objection (reconciliation report §4) and cannot be dropped without reopening it.
- **Arm B — update-disabled twin.** Answers: "does the *architecture itself* (even inert) already outperform a hand-built router, before any prospective update ever happens?" Necessary to isolate the *prospective-update* effect specifically from an *architecture* effect — without Arm B, a genuine C > A result would be ambiguous between "learning helped" and "this contextual-model shape is just better than a hand-written lookup, regardless of whether it ever updates."
- **Arm C — adaptive selector.** The treatment condition. C > B isolates the causal contribution of prospective updating; C > A (also required, per §2's exact claim) establishes that this contribution clears the bar a competent non-learning alternative sets, not merely a bar the same architecture sets against itself.

No arm is redundant: A and B share "no prospective updating" but differ in architecture (hand-built vs. learned-shape-but-frozen); B and C share architecture but differ in whether updating is enabled. Dropping any one collapses one of these two orthogonal comparisons.

## 8. Freeze the contextual champion (Arm A) and the twin's initial state (Arm B/C's `S0`)

Decided from **development-partition data only**, before the prospective phase begins:

- **Allowed features** for both the contextual champion and the selector's feature extractor: derived only from the rendered task prompt text (function name, argument names/count, natural-language spec keywords) — a fixed, versioned, hashed extractor function, identical across A/B/C.
- **Strategy/model menu**: a small, fixed set of N problem-solving strategies (§21 names this as new work — the menu's *content* is not yet designed, only its *shape*: each strategy is a distinct, fixed prompt template applied to the identical frozen model via `_ollama_query()`, never via `generate_code_from_plan()`/`deliberate_and_learn()`/`choose_model()` — see §10 for why). Fixed and identical in every arm; Arm A may use a subset or all of them via its hand-built mapping, Arm B/C's menu is identical to whatever Arm A's menu was drawn from.
- **Thresholds, tie-breaking, randomness**: any stochastic tie-break in Arm A's own routing rule (if any) or in Arm B/C's selector (e.g., epsilon-greedy or softmax sampling) is seeded per `(lineage, task_id)` using the identical matched-seed convention AP-0's own `seed_for()` already establishes — so any behavioral difference between arms is attributable to the policy, not to different random draws.
- **Fallback behavior**: a single, named default strategy for any task whose feature signature the champion/selector doesn't recognize — identical across A/B/C.
- **Retry behavior**: a fixed retry budget (recommended: 0, i.e., single-shot per decision) identical across every arm and every phase — no arm gets a compute advantage via retries.
- **Resource limits**: identical `temperature`/`num_predict`/`num_ctx` across every arm, frozen the same way AP-0's own `common.OPTIONS` is frozen — one shared constant, not per-arm tuning.
- **Feature-extractor version / classifier version**: content-hashed at freeze time (mirroring `freeze.py`'s `code_sha256` field), so a later accidental edit to the extractor is mechanically detectable, not merely assumed unchanged.
- **`S0` for Arm B and Arm C**: literally the *same* selector object, trained (in the ordinary "accumulate development-phase experience" sense) only on the DEV partition's outcomes, then frozen and content-hashed — Arm B and Arm C start from the byte-identical `S0`; they diverge only in whether `update()` is a no-op (Arm B) or live (Arm C) during the prospective phase.
- **No prospective tuning of any of the above**: once the prospective phase begins, none of these constants may change for any arm, for any reason, including a poor-looking early result.

## 9. Freeze other experience channels

Every channel independently identified across the reconciliation report, the evaluator-qualification report, and a fresh source check this session:

| Channel | Status | Basis |
|---|---|---|
| `self_edit_attempt_ledger.py` / `initial_f2_error` | **EXCLUDED** | The harness never calls `execute_self_edit()`, `generate_code_from_plan()`, or `read_recent_f2_error()` — generation is a direct, fixed-prompt `_ollama_query()` call per strategy, confirmed by re-reading `_ollama_query()`'s own signature/docstring this session: no ledger read, no RiverBrain call, no memory call anywhere in its body. |
| RiverBrain / `model_task_stats` | **EXCLUDED** | The harness never calls `get_river_brain()`, `choose_model()`, or `deliberate_and_learn()` — confirmed by design (§10), not merely by omission. |
| Council statistics / `council_rater.py` / `is_council_trusted()` | **EXCLUDED** | No council deliberation of any kind — one fixed model, one direct call per decision. |
| Task-type classifier (`task_type_classifier.py`) | **EXCLUDED** | Task type is fixed by construction (the experiment's own defined task family); nothing calls `detect_task_type()`/`resolve_task_type()`. Re-read the module's own header this session — it is explicitly a fallback signal for `detect_task_type()`'s low-confidence path, which this harness never invokes. |
| `self_edit_convergence.json` / non-convergence streak tracking | **EXCLUDED** | Not a self-edit pipeline call. |
| `self_edit_outcome_tracker.py` | **EXCLUDED** | Same reason. |
| Retrieval / `memory_bridge.retrieve_relevant_memories()` | **EXCLUDED, with the verification stated plainly**: `_ollama_query()`'s own body (re-read this session) constructs its request from the `prompt`/`system` arguments the caller supplies directly — it does not call into `memory_bridge` anywhere in its own code. The harness must supply a fixed, static prompt per strategy with no memory-retrieval step of its own. |
| Prompt/conversation history | **FROZEN IDENTICALLY** — single-shot, stateless generation per decision; no multi-turn history is used by any arm, so there is nothing to freeze differently. |
| Ollama's own internal `_ollama_query()` circuit breaker | **UNKNOWN — flagged, not assumed.** `_ollama_query()`'s docstring states it "scopes the circuit breaker to (model, task_type)," but a targeted search of `river_deliberation.py` for `circuit_breaker`/`_CIRCUIT`/`CircuitBreaker` found no definition in that file — the mechanism is implemented elsewhere or under another name and was not traced further in this pass. **This must be resolved before implementation**: if it is in-memory-only and scoped per-process, it interacts with the restart-boundary design in §11 (a fresh process would reset it, which is probably fine) but if it is file-persisted, it is a real, currently-unaccounted-for shared channel between arms and must be either given a fixed, harness-local task_type key that never collides across arms, or bypassed entirely. |
| Ollama server-side response caching, if any exists at the given `temperature` | **UNKNOWN** | Not verified in this pass; flagged as a dev-phase check (confirm two identical calls with different nonces/nothing-changed produce independently-sampled, not cached, outputs at the frozen `temperature`). |
| The experimental selector's own persisted state | **EXPERIMENTALLY CONTROLLED** — this is the treatment variable itself: frozen (`S0`, no updates) for Arms A/B, live-updating (`S0→S1`) for Arm C. This is the one channel that is *supposed* to differ, and its difference must be the *only* difference. |

**No hidden adaptive channel may differ between arms without being part of the stated treatment** — the table above is the complete accounting; anything not listed and later found to differ between arms invalidates the run.

## 10. Influence-provenance chain

Minimum linked records, explicit foreign keys throughout, no reliance on timing/ordering alone (directly closing the reconciliation report's §6 "which outcome caused this update" requirement):

- **E (evaluated experience)**: `{experience_id, lineage_id, task_id, task_feature_signature, strategy_used, oracle_outcome: PASS|FAIL, timestamp}` — written once per completed prospective-phase decision, by the harness controller, never by the selector itself.
- **U (update)**: `{update_id, experience_id (FK→E), pre_state_hash, post_state_hash, selector_code_version_hash}` — written by the selector's own `update()` call, wrapping every state mutation; `pre_state_hash` and `post_state_hash` are content hashes of the full persisted state, so a no-op update (Arm B, by construction) is mechanically verifiable as `pre_state_hash == post_state_hash` for every single call, not merely asserted from source-reading the "disabled" flag.
- **S (selector state)**: the on-disk state file itself, content-hashed at every save; `S0` = the hash recorded at the end of the development phase (identical file for Arm B and Arm C); `S1` = the hash recorded at the end of the prospective phase for Arm C only (Arm B's file must hash-equal `S0` at every checkpoint, per the `U` record's own guarantee above).
- **D (later decision)**: `{decision_id, lineage_id, arm, holdout_task_id, state_hash_used, task_feature_signature, strategy_selected, selection_probability (if stochastic), random_seed_used}` — one record per holdout-phase decision, for every arm.
- **execution**: `{decision_id (FK→D), candidate_code_hash, generation_time, model_digest}`.
- **O (outcome)**: `{decision_id (FK→D), oracle_pass_fail, evaluator_nonce, evaluator_code_version_hash, timestamp}`.

Every record is written by the harness controller (a trusted wrapper, mirroring `self_edit_attempt_ledger.py`'s own "trusted wrapper, not the untrusted generated content" discipline established earlier this session), never by the selector or the generation call itself, and no record's presence or absence is ever inferred from another record's timestamp alone.

## 11. Experience-substitution intervention

Tests whether the **content** (not merely the occurrence) of an evaluated outcome caused a given update — Codex's intervention 1.

**Design: record once, replay twice from checkpoint `S0` — never re-run real generation twice.** Running the prospective phase independently for a TRUE condition and a counterfactual condition would reintroduce real sampling variance as a confound (a different random draw could produce a different candidate, a different oracle outcome, and a cascading different trajectory, for reasons having nothing to do with the substitution being tested). Instead: run the real prospective phase exactly once for Arm C, recording the full, ordered trace of `(task_id, strategy_selected, generated_candidate, real_oracle_outcome)` tuples. Then construct a second, purely mechanical lineage — **SHAM-REVERSED** — that replays this identical recorded trace from the identical `S0` checkpoint, but flips every `oracle_outcome` label fed to `update()` (PASS reported as FAIL and vice versa). No new generation, no new oracle call — this is pure state-machine replay against a fixed, already-real recorded history.

**Explicit, stated handling of nonlinearity, per the mission's own caution not to assume subtraction reconstructs a counterfactual**: because `update()` changes `S`, and the *next* decision's strategy selection can depend on `S`, the TRUE and SHAM-REVERSED lineages will genuinely diverge in *which task-strategy pairs occur* from the first substituted update onward — this is not an artifact to correct, it is the correct and intended behavior of the intervention (a real learner exposed to flipped feedback should end up making measurably different choices, not identical ones). **The comparison this intervention supports is therefore at the outcome level, not the per-step-state level**: compare the TRUE lineage's `S1` against the SHAM-REVERSED lineage's own final state, `S1'`, on the same fixed holdout set (§13/§14). If TRUE's `S1` produces materially better holdout performance than SHAM-REVERSED's `S1'`, that is evidence the *content* of the real outcome, not merely the act of updating, drove the benefit. If TRUE and SHAM-REVERSED perform indistinguishably, the update mechanism is not sensitive to outcome content at all (a real, informative negative finding, not a design failure).

## 12. State-substitution intervention

For a fixed holdout task, hold identical: the task, the feature extraction, the strategy menu, all constraints/budgets, and the random seed used for any stochastic tie-break. Then run the *same frozen selector code* twice — once loading `S0`, once loading `S1` — and record three distinct causal observables, ranked from weakest to strongest per the mission's own instruction not to promote a rung:

1. **Score/value change** per strategy (weakest — a numeric shift with no behavioral consequence is not evidence of influence).
2. **Selection-probability change** per strategy, if the selector is stochastic (intermediate — a real distributional shift).
3. **Selected-action change under matched randomness** (strongest — with the identical seed used for both the `S0` and `S1` runs, does the *actual chosen strategy* differ?).

**A materiality threshold is pre-registered, not left to be decided after seeing results**: a probability shift or score shift must exceed a magnitude derived from development-phase variance (the natural noise floor of repeated identical `S0` scoring runs) before being counted as "meaningfully different." A technically-nonzero but noise-floor-sized shift does not count as behavioral influence, per the mission's own explicit instruction.

## 13. Persistence/restoration intervention

**A save call is explicitly not sufficient** — the intervention requires a genuine, multi-process restart boundary, mirroring the standard this project's own Tier-8 forensic finding already established for a different mechanism (RiverBrain's background writer thread) as the bar for "actually persisted," not merely "an in-memory object that happens to still be alive."

1. Development-phase process (Process 1) writes `S0` to disk, hashes it, and **exits.**
2. A fresh process (Process 2) — no shared memory, no shared object references with Process 1 — loads `S0` from disk, runs the real prospective phase, writes `S1` to disk, hashes it, and **exits.**
3. A fresh process (Process 3) loads `S1` from disk and runs the holdout-phase decisions for Arm C, producing the observed C-arm holdout result.
4. **Replacement test**: a fourth fresh process (Process 4), identical code to Process 3, loads `S0` instead of `S1` and re-runs the identical holdout decisions (same seeds). The observed effect (whichever C-vs-B/A advantage was found) must **disappear**, reproducing Arm B's own performance level — not some third, unexplained result.
5. **Restoration test**: a fifth fresh process (Process 5), loads `S1` again and re-runs the identical holdout decisions. The effect must **reappear, deterministically identical** to Process 3's result (given matched seeds), confirming the round-trip is genuinely mechanical, not a one-off artifact of Process 3's specific runtime state.

This five-step chain — effect present with `S1` → effect absent with `S0` substituted → effect reappears identically with `S1` restored — is the mechanical, falsifiable bar for "persistence was causally load-bearing." A design that only performs step 3 (load `S1` once, observe a good result) has established nothing beyond "a file existed and was read" — exactly the gap this section exists to close.

## 14. Independent outcome comparison

Arms A/B/C are run against the **identical** frozen holdout task set, identical model+digest, identical strategy menu, identical generation/retry budget, identical context (none — stateless single-shot calls), no tools, identical evaluator (`oracle_runner.grade()` with fresh nonces per call), identical token/call-budget metering (every real backend call's token count and wall-clock time logged per decision, per §10's `execution` record). **Primary outcome**: holdout PASS rate per arm, per split (T/S/NEAR/UNREL), computed at the lineage level (§3/§18) not the pooled-task level. **Acquisition cost is measured and reported separately, never silently absorbed into the correctness comparison**: Arm C's real backend-call count/token spend/wall-clock time during the *prospective* phase is logged and reported alongside the holdout result — Arms A/B spend zero prospective cost by construction (frozen from development data alone), so any observed C advantage must be reported honestly as "achieved at a real, measured, non-zero acquisition cost," not presented as a free win. The holdout-phase budget itself (where the actual correctness comparison happens) is matched exactly across all three arms — this is the fairness contract's load-bearing guarantee (§17), not the prospective-phase cost, which is asymmetric by design and disclosed as such.

## 15. Structural-transfer interpretation

Already specified precisely, per split, in §4 — restated here as the pre-registered interpretation table this section asks for directly:

| Evidence pattern | Interpretation | Pre-registered before data exists |
|---|---|---|
| C > A, C > B on T only; S/NEAR/UNREL flat | Repetition-level effect | Weakest positive result; does not support the bounded claim as stated in §2 |
| C > A, C > B on S; NEAR/UNREL flat | **Structural transfer** | This is the pattern that supports the exact bounded claim in §2 |
| Any arm shows unwarranted improvement on NEAR | Overgeneralized/non-discriminating routing | Reported as a negative/cautionary finding regardless of S/T results — this pattern actively *undermines* a claim of genuine feature-conditioned learning |
| Any arm shows improvement on UNREL | Confound (warm-up, formatting artifact, non-specific drift) | Investigated before any positive claim is accepted from the same run; not folded into any transfer claim |
| No split shows any C advantage over both A and B | No prospective-update advantage established | The honest, useful negative result the mission explicitly asks this design to remain capable of producing |

"Repetition" is defined as: same template/kind as trained on, fresh instance (never-seen exact input tuple, since literal-instance reuse would be memorization, not even repetition). "Narrow/structural transfer" is defined as: same underlying skill, materially different input representation (S split, per `tasks_v2.py`'s own S-template design — tuples vs. dicts, parsed strings vs. structured records). "Unrelated transfer" and "failure to transfer" are the UNREL and null-result rows respectively. These definitions are AP-0's own actual construction semantics (re-read directly from `tasks_v2.py` this session), not a generic assumption imported from elsewhere.

## 16. Fairness/resource contract

Matched, exhaustively, across every arm for the holdout-phase comparison specifically (§14): task distribution (identical frozen set), models (identical digest, pinned at freeze time), strategies (identical menu), generation budget (identical `num_predict`/`temperature`/`num_ctx`), retry budget (identical, recommended 0), context (none, stateless), tools (none), hidden evaluator (identical `oracle_runner.grade()` invocation shape), backend configuration (identical Ollama server, identical options dict), token/call budget (logged per decision, verified balanced post hoc — a formal balance check, the same discipline a randomized trial applies to its own baseline covariates, not assumed a priori). Any post hoc imbalance found in this check is reported as a confound requiring explanation, not silently absorbed into the result.

## 17. Statistical plan

- **Primary outcome**: holdout PASS-rate difference, Arm C minus Arm B, on the **S** split — the direct operationalization of the bounded claim in §2.
- **Secondary outcomes**: C vs. A on S; C vs. A/B on T (repetition, weaker evidence); C vs. A/B on NEAR (specificity check, pre-registered expectation: null or negative); C vs. A/B on UNREL (confound check, pre-registered expectation: null).
- **Unit of analysis**: replicate lineage (§3) — a cluster-robust or mixed-effects estimator treating lineage as the clustering/random-effect unit, holdout task instances within a lineage as correlated sub-observations, not independent Bernoulli trials.
- **Sample-size rationale — stated honestly as currently unjustifiable without a pilot**: this project's own existing evidence (Architecture A's n=12/one-mined-problem null result; Tier-4's n=84 architecture-level McNemar comparison landing at p=0.087, short of significance) both suggest that real effect sizes in this general regime, for this model family, are small if they exist at all. **A dedicated pilot is required before committing to a final lineage count**, specifically to estimate: (a) the real between-lineage variance in holdout PASS rate (needed for the cluster-level power calculation), and (b) a realistic point-estimate of the C-vs-B PASS-rate gap on the S split, from a small number (recommended: 3-5) of real, complete, low-stakes pilot lineages run at a coarse task-set scale before the final frozen holdout set is drawn at full size.
- **Stopping rule**: the number of replicate lineages is fixed *before* the confirmatory holdout phase begins, based on the pilot's power estimate — no optional stopping, no adding lineages after seeing early holdout results.
- **Exclusions**: infrastructure failures (timeout, connection error, classified via `oracle_runner.grade()`'s own `infra`/`timeout` fields) are excluded from the correctness denominator but their *rate* is compared across arms — an imbalanced infra-failure rate is itself a reportable confound, not silently dropped. Duplicate or near-duplicate holdout instances are checked (input-tuple equality, mirroring `make_cases2()`'s own `seen`-set deduplication) and removed before freezing. A harness-side crash (not a candidate failure) is excluded from the outcome count and logged separately — never silently counted as FAIL, which would conflate harness bugs with genuine task incorrectness — and this exclusion rate must also be balanced across arms.
- **Uncertainty reporting**: Wilson confidence intervals per arm per split at the pooled-task level (reusing `qual.py`'s own `wilson()` formula verbatim, a proven, already-used precedent in this exact package) presented alongside, not instead of, the primary cluster-level estimate.

## 18. Predetermined interpretation matrix

The mission's own seven rows, filled in against this design's concrete arms and interventions:

1. **Adaptive (C) does not beat update-disabled twin (B)**: no prospective-update advantage established — the experiment ends here, honestly, as a real negative result.
2. **C beats B but not frozen champion (A)**: prospective updating had a measurable effect, but the resulting policy still does not clear the bar competent static engineering already sets — a genuine, reportable, non-trivial finding (architecture-plus-updating still loses to good hand-built routing), not a null result to bury.
3. **C beats both before restart, but the advantage is absent post-restart** (checked via §13's replacement/restoration chain): within-run adaptation only, no genuine persistence — falsifies the persistence half of the bounded claim specifically.
4. **Benefit survives restart, but §12's state-substitution test shows no meaningfully different selected action between `S0` and `S1`**: persistence exists mechanically, but causal behavioral influence is not established — the state is there, but it isn't doing the work the naive holdout comparison implied.
5. **State substitution changes decisions, but hidden correctness does not improve**: causal behavioral influence without competence improvement — a real, interesting, reportable dissociation (the state is causally load-bearing, but the direction it pushes decisions isn't a good one).
6. **C beats both controls on T only**: narrow, repeated/familiar-structure effect — reported as such, not inflated to a transfer claim.
7. **C beats both controls on the S (appropriate held-out structural) split, with NEAR/UNREL flat**: the strongest result this design is capable of producing — evidence for bounded, persistent, experience-derived structural transfer, exactly and only the claim stated in §2. No stronger claim is licensed by this result, regardless of how clean it looks.

## 19. Leakage attack

Worked through the mission's full list, against this specific design:

- **Hidden expected-value / stdout/stderr leakage**: closed by §6's sanitized-feedback contract — `update()` and every persisted record never receive `output_tail`/`error_tail`/expected values, only the boolean outcome. This directly incorporates the evaluator-qualification report's own named risk (both `oracle_runner.grade()` and `objective_verify()` return truncated tails that could echo assertion fragments) as a hard exclusion, not a hoped-for discipline.
- **Task IDs**: the selector's feature signature is derived only from rendered prompt text (§6/§9), never from internal task IDs or split labels — confirmed by `tasks_v2.py`'s own construction (`spec` text never embeds the internal `task_id`, per direct read this session).
- **Procedural seeds / repeated templates**: DEV/PROSPECTIVE/HOLDOUT seed ranges must be disjoint, and no literal input-tuple instance may be shared across partitions — checked mechanically at freeze time, mirroring `qual.py`'s own real, already-exercised cross-file token-overlap assertion (`assert not (used & prev)`).
- **Evaluator traces**: see the first bullet.
- **Prompt history**: none exists (§9/§10 — stateless single-shot calls).
- **Current-error feedback**: explicitly excluded by §6's contract (coarse failure class is a considered-and-declined extra bit, not merely absent by oversight).
- **Classifier/RiverBrain updates, cache contamination**: excluded by §10's channel table — this harness never touches either.
- **Unequal retries/model calls/token budgets**: closed by §17's fairness contract and its logged, post hoc balance check.
- **Researcher intervention / post-hoc exclusions**: closed by the freeze-and-hash-and-assert pattern (§5, reused from `freeze.py` verbatim) plus §18's fixed, pre-registered interpretation matrix — there is no discretionary step between "see the data" and "report the finding."
- **Accidental access to candidate evidence**: this harness must use its own, dedicated log files — never `memory/self_edit_attempt_ledger.jsonl`, never `memory/river_brain.pkl` — an explicit design requirement, not an assumption; reusing either file, even read-only, would risk the write-only/no-read invariant established earlier this session for a different, unrelated purpose.
- **AP-0 artifacts accessible outside jail**: this experiment requires its **own** `jail.py`-style profile, scoped to its own experiment root and denying read access to AP-0's own `stage0`/`v2` roots (and vice versa) — the two missions are unrelated and must not share a jail boundary even though they share the underlying mechanism's code.

**No leak found in this pass that the design above does not already close** — the one item requiring further work before implementation, not closed by design alone, is the UNKNOWN circuit-breaker channel flagged in §9, which needs to be traced to its actual definition before this leakage analysis can be called complete.

## 20. Minimum implementation surface

| Component | Classification | Basis |
|---|---|---|
| `oracle_runner.grade()` | **ALREADY EXISTS** | Reused verbatim, per the evaluator-qualification report. |
| `worlds.py` (procedural convention generation) | **ALREADY EXISTS** | Kind-agnostic, directly reusable with a fresh seed range. |
| `tasks_v2.py`'s T/S/NEAR/UNREL construction + `make_cases2()` | **ALREADY EXISTS** | Reused verbatim for hidden-test generation. |
| `jail.py`'s `profile()`/`run_jailed()` | **ALREADY EXISTS**, needs a new invocation | Generic, already parameterized by `arm_root`/`exp_root`; a new profile instance scoped to this experiment's own root is configuration, not new code. |
| `freeze.py`'s hash-and-assert pattern | **ALREADY EXISTS**, needs a new invocation | Reused structurally; new artifacts to hash, same mechanism. |
| `oracle_b_v2.py`'s independent-reference pattern | **ALREADY EXISTS** as a template | A second reference implementation must be authored for this experiment's own task templates, following this file's existing shape. |
| `_ollama_query()` standalone callability | **ALREADY EXISTS** | Proven reusable per `run_capability_pilot.py`'s own RAW condition and this session's own re-read of its signature. |
| `wilson()` CI helper | **ALREADY EXISTS** | Reused verbatim from `qual.py`. |
| Strategy menu (fixed prompt templates) | **REQUIRED, new** | Content not yet designed — the shape (N fixed templates, one direct `_ollama_query()` call each) is specified, the specific N strategies are not. |
| Standalone, file-persisted selector (lookup-table architecture recommended for the minimal version) | **REQUIRED, new** | Modeled structurally on RiverBrain's per-`(context, strategy)` incremental-mean shape, but a wholly separate object/file — no shared state with production RiverBrain, ever. |
| Sanitized-feedback extraction function | **REQUIRED, new** | A few lines: pulls `passed` only from `grade()`'s return dict, discards everything else before it ever reaches the selector. |
| E/U/S/D/O provenance-record schema + logger | **REQUIRED, new** | Modeled on this session's own candidate-logging implementation discipline (write-only, narrow, never read back into generation) — a new, dedicated JSONL, never an existing production or AP-0 log file. |
| Replay-from-checkpoint harness (§11) | **REQUIRED, new — the single most novel piece of engineering this design needs** | Nothing in this repository currently replays a recorded decision trace against a substituted-label update stream; must be built and independently verified (its own `scripts/verify_*.py`-style test suite, per this project's own standing discipline) before use, since a bug here would silently reconstruct the wrong counterfactual. |
| Multi-process restart-boundary controller (§13) | **REQUIRED, new** | Small but genuinely new — a CLI-phase controller in the shape of `qual.py`'s own multi-phase (`build`/`freeze`/`construct`/`gate`/`analyze`) structure, but driving real process exits/relaunches between phases rather than function calls within one process. |
| New `jail.py`-style profile for this experiment's own root | **REQUIRED, near-zero new code** | `profile()` is already generic; only a new root path needs to be supplied. |
| Richer sanitized feedback (coarse failure class) | **OPTIONAL** | Explicitly declined in §6 as not required for this rung; noted here only because the mission asks every candidate to be classified, not because it is recommended. |
| A contextual-value-model selector (vs. lookup table) | **OPTIONAL** | More expressive, more implementation risk, not required for the minimal claim; deferred to a later rung if the lookup-table version's feature space is judged too coarse after a pilot. |

## 21. Singularity Archaeology sanity check

**A system can be constructed that passes this experiment indefinitely and cannot progress toward open-ended accumulated competence — and it is, in fact, very close to what the recommended minimal implementation (§20's lookup-table selector) would look like if built the straightforward way.** A selector that is literally a finite lookup table over a closed, fixed feature space (derived once, frozen, never re-derived from experience) and a closed, fixed strategy menu (no mechanism to propose a new strategy, ever) can, in principle, perfectly learn which of its N fixed strategies wins for which of its M fixed feature buckets, converge to that optimum, and keep passing this exact experiment forever — without ever (a) discovering or proposing a strategy outside its predefined menu, (b) expanding or refining its own feature representation from experience (no representation learning, only re-weighting over a static representation), or (c) improving any individual strategy's own ceiling, which remains fixed by the underlying frozen model's raw capability regardless of how well the selector learns to route to it.

**Stated plainly, not softened**: this experiment, even at its cleanest possible positive result (§18's final row), establishes exactly one rung — "retained experience can cause persistent, causally-verified improvement in *choosing among existing options*." It is a real, necessary prerequisite for anything higher on the ladder (a system that cannot even do *this* certainly cannot do more), but it provides **zero evidence** toward the two capabilities that would actually be required for open-ended accumulated competence: generating genuinely new strategies (not re-weighting a fixed menu) and expanding its own representation of the problem space (not re-scoring a fixed feature bucketing). The missing capability, named directly: a mechanism that can propose and evaluate *novel* candidate strategies outside its starting menu, and revise *what it pays attention to* (its feature extractor), not merely *how it weights* what it already extracts. Neither is attempted here, by this design's own explicit and correct scoping (§2's exclusions already say as much) — this section exists only to locate the rung, not to raise the claim.

## 22. Remaining blockers

1. The strategy menu's actual content is not yet designed — only its shape (§8/§20).
2. The selector architecture (lookup table vs. a richer contextual model) is not yet chosen — a lookup table is recommended for this minimal rung; §21 above states plainly what such a choice cannot demonstrate.
3. No pilot data exists to justify a final sample size (§17) — this must be run and analyzed before the confirmatory holdout phase is frozen.
4. The `_ollama_query()` circuit-breaker channel (§9) is UNKNOWN, not EXCLUDED — must be traced to its real definition and either neutralized or shown to be harmless before implementation.
5. The replay-from-checkpoint mechanism (§11) and the multi-process restart controller (§13) are both genuinely new engineering with real correctness risk and require their own independent verification suites before being trusted for anything.
6. AP-0's own qualification run is still in progress in this same session as this document is written — whether it leaves behind a disjoint, reusable seed-range/template-set convenient for this experiment (versus this experiment needing to draw its own from scratch, which the design already assumes) is not yet known and does not block this design, but should be checked once AP-0 concludes.

## 23. Final recommendation

The protocol is complete, internally consistent, and reuses proven infrastructure everywhere it exists rather than inventing parallel machinery — the one place genuinely new engineering is required (the replay-from-checkpoint and restart-boundary harnesses) is named precisely, not glossed over, and neither is exotic relative to patterns this project already trusts elsewhere (AP-0's own multi-phase, freeze-then-run CLI structure; this session's own candidate-logging write-only discipline). This design is ready to be handed to an adversarial review pass — that is the correct next step, not implementation. Implementation remains not authorized.

---

**TASK CORRECTNESS:** QUALIFIED

**ARTIFACT PROVENANCE:** SUFFICIENT

**INFLUENCE PROVENANCE DESIGN:** QUALIFIED

**FIXED CONTEXTUAL CONTROL:** QUALIFIED

**UPDATE-DISABLED TWIN:** REQUIRED

**EXPERIENCE-CHANNEL ISOLATION:** CONDITIONAL

**STRUCTURAL TRANSFER TEST:** QUALIFIED

**PREREGISTRATION COMPLETENESS:** PARTIAL

**READY FOR ADVERSARIAL REVIEW:** YES

**IMPLEMENTATION AUTHORIZATION:** NO

**1. What exact positive claim could this experiment establish?** That a standalone, isolated selector's ability to route among a fixed menu of coding strategies for a fixed task family was causally, persistently improved by retained, independently-evaluated prospective experience — beyond what a competent, development-selected fixed router and an architecturally identical non-updating twin could achieve — verified via genuine restart survival and direct state-substitution, on structurally-related-but-non-identical (S-split) holdout instances.

**2. What is the strongest alternative explanation it still cannot eliminate?** That the "learned" routing table is, functionally, a fitted lookup table over a task-signature space narrow and recurring enough that a sufficiently thorough human, given the same development data, could have hand-built an equally good static router — the fixed-contextual-champion arm (A) is specifically designed to test this, but if Arm A's own construction is not genuinely as competent as it could be (a real risk in any experiment where the "best static effort" is authored by the same team running the experiment), a positive C-vs-A result could still partly reflect an under-engineered Arm A rather than a genuine ceiling on static routing.

**3. What is the smallest missing prerequisite?** A resolved answer to the UNKNOWN `_ollama_query()` circuit-breaker channel (§9) — every other blocker (strategy menu content, selector architecture choice, pilot sizing, the two new harness components) is either a designed-but-unbuilt artifact or a deliberate, disclosed next step; this one is a genuine unresolved fact about the current codebase that could silently violate the experience-channel-isolation guarantee this whole design depends on.

**4. Where does this experiment sit on the backward path from hypothetical open-ended accumulated competence to FeralEcho today?** Very near the bottom, and deliberately so — it is the first rung above "no retained state has ever been shown to causally improve a decision after a real restart" (which is, per the reconciliation report, roughly where FeralEcho's own production self-edit/RiverBrain machinery honestly stands today). A positive result here would establish that *retained-state-causes-better-routing* is achievable in principle, in an isolated, minimal substrate — necessary evidence before ever asking whether production Echo does anything like it, and light-years short of strategy generation, representation learning, or anything resembling open-ended accumulated competence.
