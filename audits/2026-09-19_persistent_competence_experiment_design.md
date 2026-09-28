# Persistent, Accumulated, Experience-Dependent Competence — Experiment Design

**Date:** 2026-09-19
**Type:** Investigation + reconciliation (read-only; no experiment executed by this mission)
**Evidence ledger:** `audits/2026-09-19_persistent_competence_experiment_design_evidence_ledger.json` (32 records, IDs `pce-001`…`pce-032`, cited inline below as `[pce-NNN]`)

---

## 1. Executive Verdict

**FeralEcho has one mechanism — RiverBrain's `learn() → model_task_stats → score_model() → council ranking` chain — with a VERIFIED causal link from a state mutation to a changed selection decision** `[pce-001, pce-032]`. That is real, reproducible, and architecturally current as of this session's own direct source read. **It is not, currently, evidence of genuine competence.** The feedback signal that populates the connected state is a static, self-computed AST-complexity heuristic (`_score_response_quality`) or a blend that is still 70%-anchored to that same heuristic `[pce-002]`. The one genuinely independent, already-implemented signal in the same class — real sandboxed code-execution pass/fail (`learn_from_sandbox_outcome`) — is confirmed, by four independent reads using two different methods, to be architecturally disconnected from the statistic that drives selection `[pce-003, pce-011, pce-032]`. Separately, where RiverBrain's learned score *has* been tested against a genuinely independent criterion in production code, it failed — worse than chance once a confound was removed `[pce-031]`.

No mechanism anywhere in this extensively-audited codebase (roughly 300 prior audit files, five parallel and independently-converging investigations run for this mission, plus this session's own direct checks) has ever been shown, by a real controlled experiment, to improve measurably against an independent criterion **across multiple real accumulated episodes**. The closest thing that exists — a genuinely causal, restart-surviving, longitudinal, adversarially-hardened demonstration of exactly this shape — was built and run, but on an isolated, authored, non-Echo three-worker fixture, not on live FeralEcho `[pce-012, pce-013, pce-014]`. `task_type_classifier.py`, the other real candidate learning mechanism, lands at L2 (behavioral adaptation), not L3: its training label is ~99.5% mechanically reproducible from the heuristic it's meant to replace, with a confirmed circular self-training path `[pce-005, pce-006]`.

**The central, load-bearing fact this whole design rests on**: the architecture is not fundamentally incapable — the fixture experiments prove the *shape* of a real, restart-surviving, accumulating, independently-evaluated learning loop works once correctly wired `[pce-012, pce-014]` — but the live system's one VERIFIED causal mechanism is currently wired to the wrong signal. **Reconnecting an already-existing, already-computed, genuinely independent signal is the single cheapest, highest-leverage precondition for any experiment that would test real competence rather than self-referential score-following.** This report designs that reconnection and the experiment built on top of it, at the smallest scope that still supports a defensible causal claim, using only existing local infrastructure.

---

## 2. Current Learning-Path Architecture

Every currently plausible learning pathway in the repository, classified by this project's own L0–L3 vocabulary (L0 = logging only; L1 = state accumulates but has zero live behavioral consequence; L2 = a real decision demonstrably changes as a result of experience; L3 = L2 plus the driving signal is a genuine, independent evaluation, not a recording of the system's own output):

| Mechanism | Classification | Evidence |
|---|---|---|
| RiverBrain `learn()→model_task_stats→score_model()→council ranking` | **L2** (state→ranking VERIFIED; feedback signal is self-scored, not independent, so L3 is not earned) | `[pce-001, pce-002, pce-003, pce-032]` |
| `task_type_classifier.py` online NaiveBayes | **L2** (routing demonstrably changes; label ~99.5% heuristic-derived + confirmed circular self-training on ≥1 real case) | `[pce-005, pce-006]` |
| `shadow_model.py` | **L1** (real persisted calibration data, zero live consequence; explicitly, deliberately retired 2026-09-13; unchanged in the current uncommitted diff) | `[pce-019]` |
| `self_edit_attempt_ledger.jsonl → generation prompt` | **L1, edge of L2** (wiring VERIFIED correct under adversarial testing; downstream quality effect explicitly untested — UNKNOWN) | `[pce-018]` |
| `echo_state.py` dim[8] valence → 3 real consumers | **SUPPORTED, not experimentally reached L2** (formulas traced exactly; no execution performed) | `[pce-023]` |
| `seam_engine.py` / `curiosity_engine.py` / `garden_manager.py` | **L0/L1 — ruled OUT** (real logging + real topic-selection action, zero measured competence consequence anywhere) | `[pce-024]` |
| `memory_bridge.py` FAISS retrieval | **Architecturally retrieval, not learning — ruled OUT** regardless of the ablation's statistical power | `[pce-025]` |
| E5-mini (`app/experiments/e5_mini/`) | **Not executed; targets a different question (one-shot transfer, L4 in its own separate vocabulary) than accumulation; measurement instrument itself DISPROVEN as qualified** | `[pce-008, pce-009, pce-010, pce-028]` |
| RAOC (`app/experiments/raoc/`) | **Stuck at a 12-trial, explicitly non-evidentiary pilot** | `[pce-027]` |
| `preference_provenance/` | **Apparatus exercised (56 real trials exist); no reviewed verdict exists — UNKNOWN** | `[pce-026]` |
| `provenance_check.py` | **Real, tested, dormant (zero production callers); answers file/process identity, not content-provenance of learned state** | `[pce-021, pce-022]` |
| Isolated fixture (recursive-learning-ground-truth R3/R4/R6) | **L3, demonstrated — but not inside FeralEcho/Echo itself** | `[pce-012, pce-013, pce-014]` |

**Reconciliation with the project's own prior claim**: `CLAUDE.md`/this project's forensic-audit skill both cite Mission 31 (`audits/2026-09-09_open_ended_learning_discovery.md`) as "this project's cleanest current example" of a VERIFIED L3 mechanism. This mission's investigation **confirms** the VERIFIED causal-mutation claim but **narrows** the L3 attribution: Mission 31's own test deliberately injected a hand-constructed "excellent"/"terrible" label to demonstrate the mutation mechanics work — it did not, and does not claim to, establish that the *live* feed populating that mutation is itself independent. Three parallel investigators and this session's own direct read all independently reached the same correction. This is recorded here as a **DISPROVEN**-flagged correction to an implicit over-reading of a real prior finding, not a correction of Mission 31's own explicit claims, which were accurately scoped.

---

## 3. Producer→Consumer Wiring Evidence

Per this skill's own standing discipline, producer and consumer both existing is not evidence of a wire — the actual connection was traced for every candidate:

- **RiverBrain**: producer `learn()` (`app/core/echo_model_orchestrator.py:808`) → writes `model_task_stats[model][task_type]` → consumer `score_model()` (line 995) reads it → consumed by `_select_council()` (`river_deliberation.py`) and `rank_models()`. **Wire confirmed real** `[pce-001, pce-032]`. A second producer, `learn_from_council_rating()` (line 936), also writes the same field, gated behind `is_council_trusted()`, blended 30/70 with the same non-independent scorer `[pce-002]`. Two producers that exist but do **not** write this field, confirmed by direct negative grep: `learn_from_sandbox_outcome()` (line 870) and `learn_from_rating()` (line 898) `[pce-003, pce-032]` — these are real, live, called-in-production methods whose outputs never reach the consumer that matters.
- **`task_type_classifier.py`**: producer = real user/system interactions → labeled via `compute_intent_heatmap()`'s heuristic in 99.5% of the real training corpus → consumer = `resolve_task_type()`'s override path. **Wire confirmed real, but the label itself is not an independent producer** `[pce-005]`.
- **`echo_state.py` valence**: producer = 3 real input sources (self-edit deltas, council-rating average, Optuna dry-run deltas) → `dim[8]` → three distinct real consumers with exact formulas cited (`river_deliberation.py:263-270,1254`, `echo_optuna.py:23-32`, `emergent_scheduler.py:574-581`). **Wire SUPPORTED by static trace, not yet VERIFIED by execution** `[pce-023]`.
- **`seam_engine.py`/`curiosity_engine.py`**: producer = real detection/scoring → consumer = `garden_manager.harvest_question()`/`select_from_garden()` → **the wire terminates at "becomes a prompt string"** — traced exhaustively, no further consumer compares outcomes. **Confirmed absent as a competence wire** `[pce-024]`.
- **`self_edit_attempt_ledger.jsonl`**: producer = real self-edit attempt outcomes → consumer = `_attempt_ledger_evidence_section()` in the generation prompt. **Wire confirmed real and adversarially tested for correct delivery** `[pce-018]` — but the wire's *effect*, i.e. whether delivered evidence changes generation quality, was never measured. This wire delivers content into a prompt, which is architecturally the same class of mechanism as retrieval — see §6 for why that matters.
- **`provenance_check.py`**: producer = real OS/git facts → consumer = **none in production** `[pce-021]`. A real, tested wire with no one plugged into the other end.

---

## 4. Existing Persistent-State Inventory

| State | Location | Restart survival | Causal consequence | Evidence |
|---|---|---|---|---|
| `model_task_stats` (RiverBrain) | `memory/river_brain.pkl` | SUPPORTED (code path exists; never live-restart-verified) | VERIFIED (state mutation → ranking change) | `[pce-001, pce-004]` |
| `task_type_classifier.pkl` | `memory/` | SUPPORTED | VERIFIED under constructed ablation | `[pce-005]` |
| `self_edit_convergence.json` | repo (currently uncommitted diff shows real accumulation) | VERIFIED — re-read at process start per `CLAUDE.md`'s Self-Edit System section | Bookkeeping (names tried), not itself a competence signal | live diff, this session |
| `self_edit_attempt_ledger.jsonl` | `memory/` | Real, append-only, trivially restart-durable | Delivery VERIFIED, quality-effect UNKNOWN | `[pce-018]` |
| `shadow_self_model.json` / `shadow_accuracy.jsonl` | `memory/` | Real | **Zero** — L1, deliberately retired | `[pce-019]` |
| `echo_state_history.npy` (valence, dim[8]) | `memory/` | Real, archived per `log_retention.archive_if_due()` | SUPPORTED, not VERIFIED | `[pce-023]` |
| `memory/faiss.index` + `memory_meta.json` | `memory/` | Real | Retrieval/lookup — ruled OUT as a competence mechanism | `[pce-025]` |
| `memory/experiments/preference_provenance/raw_trials.jsonl` | `memory/experiments/` | Real, 56 real lines on disk | UNKNOWN — no reviewed verdict | `[pce-026]` |
| `memory/raoc_pilot_trials.jsonl` | `memory/` | Real, 12 lines | Explicitly non-evidentiary by the pilot's own design | `[pce-027]` |
| Fixture state (`r4_producer.json`, `r6_t0..t3.json`, etc.) | `audits/recursive_learning_ground_truth/` | **VERIFIED** — real, separate-process reload with hash confirmation | **VERIFIED** — the only fully-closed instance found anywhere | `[pce-012, pce-014]` |

**No hash/checksum manifest protects any of the `memory/` files above against silent corruption or substitution** `[pce-020]`, and `provenance_check.py`'s real, tested primitives explicitly do not reach into the *content* of these files to fingerprint their causal history `[pce-022]` — both facts are directly load-bearing for §10.

---

## 5. Strongest Currently Supported Learning Claim

Stated at the correct evidence level, not inflated and not underclaimed:

> **VERIFIED**: A specific, real FeralEcho persistent-state structure (`RiverBrain.model_task_stats[model][task_type]`) can be directly mutated and, on reload, causes a measurably different council-selection ranking, via the real production mutation formula, on a real (read-only-copied) production pickle `[pce-001, pce-032]`.
>
> **VERIFIED, but in an isolated fixture, not live FeralEcho**: when the *feeding* signal is genuinely independent and hardened against a documented shortcut failure mode, this same architectural pattern produces real, restart-surviving, multi-episode accumulating improvement against a matched no-learning control, and loses that improvement when task semantics change under a stable identifier `[pce-012, pce-013, pce-014]`.
>
> **What is NOT yet established, at any evidence level above SUPPORTED**: that the live, deployed version of this mechanism, as it actually operates today, produces genuine competence improvement rather than convergence toward whatever a static self-scoring heuristic happens to reward. `pce-031` is direct, if narrow, evidence *against* this — RiverBrain's learned score, tested against an independent criterion in one real downstream use, performed worse than chance once deconfounded.

This is the strongest claim the evidence supports, and it is a claim about **architectural capability**, not about **current, live, deployed competence**.

---

## 6. Alternative Explanations

Every one of the exclusion criteria named in the mission brief was checked against the strongest candidate mechanism (RiverBrain), not merely listed:

- **Foundation-model-native capability**: Not directly tested by this investigation; the proposed experiment (§7) controls for this via the matched no-learning control (A′), which holds model identity and prompting fixed.
- **FeralEcho architectural/scaffolding capability**: The `seam_engine`/`curiosity_engine` finding is a clean positive instance of this trap already identified and ruled out `[pce-024]` — real architecture, zero competence consequence.
- **Prompt/context effects**: `self_edit_attempt_ledger.jsonl` is the live candidate most at risk of this confound — it delivers content into a prompt, which is architecturally indistinguishable in kind from retrieval `[pce-018]`. **This mission explicitly does not select it as the primary Lizard-Tail candidate for exactly this reason** (§10). `memory_bridge` retrieval is the clean already-tested instance `[pce-025]`.
- **Retrieval of the original answer**: Directly ruled out for FAISS memory `[pce-025]`. For `model_task_stats`, the state is a running statistic, not a retrievable text of the original response — this distinguishes it structurally from a lookup-cache confound, though the underlying value it was trained on could still be interrogated for this (addressed in §7's oracle hardening).
- **Memorization**: Directly relevant to the proposed held-out task design (§7) — the task pool must include genuinely novel items not seen during any accumulation round, and a separate transfer-family task to rule out narrow memorization of the training distribution.
- **Stochastic variation**: `task_type_classifier`'s n=20 pilot flip between labelers `[pce-007]` is this project's own clean cautionary tale; the design in §7/§9 pre-registers sample sizes derived from this project's own established power-analysis practice rather than repeating a token-n pilot as if it were decisive.
- **Evaluator leakage**: This is the single most load-bearing finding of this whole investigation — `[pce-002, pce-003, pce-031]` collectively establish that the live system's one connected feedback signal is not independent, and that where independence was tested for a downstream use, it failed. Any experiment run against the live, unmodified system today would be measuring evaluator leakage, not competence, and the proposed design's Step 0 (§7) exists specifically to close this gap before any competence claim is attempted.
- **Task contamination**: The proposed design reuses the already-frozen Tier-4/Tier-5 task pool specifically because it is already known, documented, and independently audited to have real held-out discipline `[pce-015]`'s own R9 finding is the strongest available cautionary evidence — that even a "passing" result on a fixed suite can mask a real correctness gap, directly motivating the oracle-hardening requirement in §7.
- **Selection effects**: `pce-013` (the R8 shortcut finding) is a real, already-demonstrated instance of exactly this — a degenerate solution tying with a correct one under narrow training-data coverage. The proposed oracle (§7) is explicitly required to survive a replay of this exact attack before being trusted.
- **Pre-existing persistent state**: The clean-baseline condition (A) is explicitly defined as the existing, already-implemented cold-start code path (`score_model()`'s `count < _MIN_MODEL_OBSERVATIONS → 0.5` fallback), not a hand-constructed fiction — this is a real, already-verified "no experience" state, not an approximation of one.

---

## 7. Proposed Minimal Causal Experiment

### Step 0 — Qualify an independent oracle (prerequisite, not itself the competence experiment)

Given the live system's one connected signal is not independent `[pce-002, pce-003]`, no experiment run against it today can distinguish learning from self-referential convergence. The cheapest available independent signal that already exists in this codebase is real sandboxed code execution (`code_verification.py` / F2 kernel sandbox), already proven for self-edit and conversational verification. Build a task-family-scoped oracle:

- Frozen, adversarially-authored held-out test sets per task family, deliberately including broad-coverage/edge-case inputs (large integers, boundary values) specifically to catch the `pce-015` failure mode.
- Every candidate solution runs through the real F2 sandbox — never a reimplementation.
- Full execution witness logged (env fingerprint, input/output pairs, stdout hash) to an append-only, single-writer ledger.
- **Before use**: replay E5-mini's own already-built 30-fixture G0 adversarial battery `[pce-010]` plus the R8 shortcut attack `[pce-013]` and the R9 benchmark-narrowness attack `[pce-015]` against this new oracle. It must survive all of them. This reuses existing, already-built adversarial fixtures rather than re-deriving new ones — zero additional engineering cost for the hardest part of the problem.

### Step 1 — The smallest possible production change

Add a **new, parallel** field, `model_task_stats_verified[model][task_type]`, populated **only** by Step 0's independent oracle (real pass/fail), via a new `learn_from_verified_outcome()` method mirroring `learn_from_sandbox_outcome()`'s existing shape. Deliberately not a rewrite of the existing `model_task_stats["mean"]` field — this preserves current production selection behavior untouched and gives a clean, isolated intervention point. This mirrors the project's own established precedent of adding a new bucket rather than blending into an existing one when semantics differ (`self_edit_coding`, `echo_projects_coding`). `echo_model_orchestrator.py` is in `EDIT_FORBIDDEN_TARGETS` — this blocks Echo's *autonomous* self-edit pipeline only, not a human-reviewed change, but per this project's own established convention (Finding 39, Finding 46, etc.), the diff must be shown and explicitly confirmed before landing.

### Step 2 — The A/B/C/D causal experiment

See §8 for the full design; summarized here: A = cold-start baseline, B = accumulated real oracle-verified experience, C = B with `model_task_stats_verified` reset, D = a genuinely separate RiverBrain instance given only B's transplanted dict.

### Step 3 — Matched no-learning control (A′)

Identical task episodes, identical wall-clock/compute budget as B, with `model_task_stats_verified` writes disabled — isolates the state's effect from the mere effect of attempting more episodes.

### Step 4 — Novel transfer test

A held-out task family structurally different from the training distribution (e.g., a different council-relevant skill bucket, such as `echo_projects_coding` if training occurred on `coding`), directly probing whether R6 Attack 3's fixture-scope failure (task-semantics swap under a stable context defeats the mechanism `[pce-014]`) recurs in the live implementation. A genuine negative result here is valuable and must be reported as such, not smoothed over.

---

## 8. A/B/C/D State-Ablation Design

| Arm | Definition | Implementation |
|---|---|---|
| **A** | Clean baseline | Real, already-implemented cold-start code path: `model_task_stats_verified` empty → `score_model()`-analog returns neutral 0.5 for every model (architecturally guaranteed by the existing `count < _MIN_MODEL_OBSERVATIONS` fallback — no fiction required). |
| **B** | System after experience | N real held-out (but not final-evaluation) task episodes run through the real pipeline with Step 1 live; each episode's oracle-verified outcome accumulates into `model_task_stats_verified` past the `_MIN_MODEL_OBSERVATIONS` threshold. |
| **C** | B with acquired state removed | Same process/instance as B; `model_task_stats_verified` reset to the cold-start empty dict (a single, cheap, fully reversible operation); all other state (classifiers, scalers, model pool) untouched. Re-run the same held-out evaluation set. |
| **D** | Clean instance given B's state | A genuinely separate RiverBrain object/process (fresh classifiers/scalers, no shared memory) — inject **only** B's `model_task_stats_verified` dict, nothing else. Run the same held-out evaluation. |

**Predicted pattern if the claim is genuine**: B > A (significant); C regresses toward A (not necessarily identical — report residual effects from other state honestly rather than hiding them); D rises toward B using nothing but the transplanted dict.

**A note on rigor this design deliberately keeps**: unlike Mission 31's original test, this A/B/C/D design is run against the **live production evaluation loop**, with a real held-out task set, not a synthetic simulated-observation injection — closing exactly the gap `[pce-004]` flags (restart survival claimed but never live-verified) and the gap `[pce-031]` demonstrates is real (a learned score that looks causally connected can still fail an independent-criterion test).

---

## 9. Longitudinal Accumulation Design

Directly reuses R6's already-validated shape `[pce-014]`, scaled to the live system:

- **T0 → T1 → T2 → T3**, at least 4 real timepoints, each with a real Python process kill-and-restart of the component holding RiverBrain between rounds — this is the first time restart survival would be *confirmed*, not merely assumed, for this mechanism `[pce-004]`.
- Each round: a batch of real held-out episodes evaluated by Step 0's oracle, accumulated into `model_task_stats_verified`.
- **Matched controls run in parallel at every round**: (i) the no-learning control (A′, §7 Step 3), and (ii) a reversed-outcome control (feed the oracle's verdict inverted) — mirroring R6's own reversed-reward arm, which is what demonstrated the effect wasn't a monotonic-drift artifact `[pce-014]`.
- **Pre-registered success shape**: real pass-rate on the frozen held-out set should rise across T0→T3 for the real arm, stay flat or degrade for the no-learning control, and degrade for the reversed-outcome control — the exact three-way separation R6 already demonstrated in the fixture.
- **Sample size**: this project's own task_type_classifier pilot instability at n=20 `[pce-007]` and the Tier-4/Tier-5 lineage's own power-analysis discipline (documented as requiring roughly 100–500+ tasks for reliable McNemar detection at this project's observed effect sizes) argue against a token pilot being treated as decisive. Recommend: a cheap, zero-model-call harness validation pass reusing the existing fixture code `[pce-012]` first, then a properly-powered real run only after the harness itself passes Step 0's adversarial qualification.

---

## 10. Lizard-Tail Transferable-State Analysis

**Direct answer, refined from the mid-mission answer already given and now cross-checked against the completed live-wiring trace**: two real candidates exist, and neither alone is currently sufficient — this section states plainly which one this report recommends and why.

**Candidate 1 — `model_task_stats_verified[model][task_type]`** (post Step 1; today, pre-Step-1, it would be the existing but non-independent `model_task_stats[model][task_type]`): a two-field dict (`{"mean": float, "count": int}`). This is the smallest state in **real FeralEcho** with a VERIFIED causal effect on behavior `[pce-001, pce-032]`. Its removal-loses-the-effect half is effectively already demonstrated (reverting the mutation reverts the ranking). Its cross-instance-transplant half has **not** been tested — only same-object before/after mutation has. This is architecturally trivial to test (a plain picklable dict) and is the recommended primary Lizard-Tail candidate, **conditional on Step 0/Step 1 being done first** — transplanting the current, non-independent version would only prove that a self-referential preference transfers, not that competence does.

**Candidate 2 — a context-keyed outcome-preference entry** (from the isolated fixture, `[pce-012, pce-013, pce-014]`): smaller in principle, and the ONLY candidate with a fully closed removal + cross-process-transplant + independently-evaluated + longitudinally-accumulated demonstration anywhere in this investigation. It does not exist inside live FeralEcho — it is a proof that the mechanism *class* works once correctly wired, not a piece of state you can copy into `river_brain.pkl` today.

**Recommendation**: pursue Candidate 1, using Candidate 2's exact fixture methodology as the validation harness before spending real wall-clock time on live Echo (§9's sample-size discussion). This closes the gap between "smallest real-FeralEcho candidate" and "smallest properly-evidenced candidate" that currently keeps them from being the same object.

**Explicitly rejected as the primary transplant candidate**: `self_edit_attempt_ledger.jsonl` entries `[pce-018]`. Although real, wired, and persistent, this is prompt-delivered content — architecturally the same class of mechanism as retrieval (§6). A transplant "advantage" observed here could not be cleanly distinguished from a prompt/context effect without a much more elaborate control than this mission's evidence currently supports designing. `echo_state.py` valence `[pce-023]` is also rejected as a primary candidate: it is a single scalar that modulates several unrelated systems (exploration bias, sampling bounds, prompt-weight), not a task-specific competence encoding — a poor fit for "transfers a specific acquired advantage."

**The authenticity problem, stated plainly and not glossed over**: even if Candidate 1's transplant succeeds, **nothing in this codebase today could prove, to a skeptical third party, that the transplanted dict was genuinely earned through real prior episodes rather than hand-constructed to produce the desired result** `[pce-020, pce-022]`. `provenance_check.py`'s real, tested Layer 1/2 primitives verify file/process identity, not content-provenance of a learned artifact. **This is not a reason to avoid the experiment — the experiment's own internal design (real oracle logging every episode to an append-only ledger, Step 0) is itself the provenance record for the specific run.** But it does mean this mission recommends, as a small, cheap, complementary addition (not a blocker): extend `provenance_check.py`'s existing Layer-1 file-hash primitive to sha256-manifest the two small JSON artifacts this experiment would produce (the accumulated dict at each checkpoint, and the oracle's execution-witness ledger) — directly reusing existing, already-red-teamed infrastructure `[pce-021]` rather than building new provenance tooling from scratch.

**What this report will NOT call this analysis, per the mission's explicit instruction**: not reproduction, not inheritance, not instinct, not a digital organism. It is a causal state-transfer experiment on a two-field statistics dictionary.

---

## 11. Exact Metrics and Falsification Criteria

**Primary metric**: per-round pass rate on the frozen held-out evaluation set (exact binomial proportion), compared pairwise via McNemar's test (A vs. B, B vs. C, A′ vs. B) — reusing the exact methodology already validated in the Tier-4/Tier-5 capability-ceiling lineage rather than inventing a new statistical test.

**Secondary metric**: Spearman rank correlation between `model_task_stats_verified`'s model ranking and the real held-out pass-rate ranking per model — this is the single most decisive metric for distinguishing "the state changes selection" (already known) from "the state's ranking actually tracks real competence" (not yet known).

**Tertiary metric**: selection-distribution entropy across rounds (is the system converging to a stable, non-degenerate ranking, or thrashing/collapsing onto a single model — directly checking for `[pce-013]`'s shortcut-selection failure mode).

**Pre-registered falsification criteria** — the claim "FeralEcho's RiverBrain mechanism, once wired to an independent oracle, demonstrates genuine persistent accumulated competence" is **FALSIFIED** if any of:

1. B does not significantly outperform A′ (matched no-learning control) at a pre-registered threshold (exact McNemar p<0.05, one-sided, minimum N per a real power calculation before the run — not assumed from a small pilot).
2. C does not lose a significant fraction of B's gain over A (state removal doesn't remove the effect → something else, not the tested state, explains the result).
3. D does not gain a significant fraction of B's advantage from the transplanted state alone (the effect doesn't travel with the state → it's tied to the original process/context, not the state itself).
4. `model_task_stats_verified`'s ranking does not correlate with real held-out pass-rate ranking (Spearman not significantly >0) — the state changes selection but doesn't track real competence.
5. The effect fails to replicate on a second, independently-drawn held-out task pool (guards directly against `[pce-013]`/`[pce-015]`-style shortcut/overfitting).
6. The novel-transfer-family task set shows no improvement (or degrades) relative to A — any observed gain is narrow memorization of the training distribution, matching the exact failure mode already demonstrated in the fixture (`[pce-014]`'s Attack 3).

**A clean null on any of 1–6 is a valuable, reportable result**, not a failed mission — consistent with this project's own repeatedly-demonstrated discipline (`[pce-007, pce-013]`) that an honest negative is worth more than an inconclusive positive.

---

## 12. Implementation Plan Ranked by Evidence Value vs. Engineering Cost

| Rank | Item | Evidence value | Engineering cost | Notes |
|---|---|---|---|---|
| 1 | Harness validation via Candidate 2's existing fixture methodology (§10), zero real model calls | High — de-risks everything downstream | **Very low** — fixture code already exists `[pce-012]` | Do first, always |
| 2 | Step 0: build + adversarially qualify the independent oracle, replaying `[pce-010, pce-013, pce-015]`'s existing attacks | Very high — this is the precondition for any real competence claim | Low-medium — reuses `code_verification.py`/F2 sandbox, existing attack fixtures | Do second |
| 3 | Step 1: add `learn_from_verified_outcome()` + `model_task_stats_verified`, human-reviewed diff to `echo_model_orchestrator.py` | High | Low — a few dozen lines, mirrors existing method shape | Requires explicit sign-off per protected-file convention |
| 4 | Single-round A/B/C causal test (no D yet), against real held-out tasks | High | Medium — real wall-clock, no new infra | First real-system result |
| 5 | D — genuine cross-instance transplant | High (closes the Lizard-Tail question for Candidate 1) | Low once 1–4 exist — plain dict copy | |
| 6 | Longitudinal T0–T3 with real process restarts (§9) | Very high — first real restart-survival confirmation for this mechanism | Medium — requires the harness to tolerate real restarts cleanly | |
| 7 | Novel-transfer-family evaluation | High — the sharpest test against memorization | Low — reuses existing task pool infrastructure, different bucket | |
| 8 | Provenance-manifest extension for the experiment's own artifacts (§10) | Medium — strengthens the transplant claim against an authenticity challenge | Very low — extends already-tested `provenance_check.py` | Not a blocker; do alongside 4–6 |
| 9 | Liveness Ledger check for the new wire (per this project's own standing rule) | Medium — required by project convention, not optional | Low | Do once Step 1 ships |

**Deliberately not recommended in this pass**: scaling RAOC or E5-mini further (§2's inventory already shows both are answering different questions from the one this mission was asked about, or have a disqualified measurement instrument); adopting `river.bandit` `[pce-016]` before a simpler baseline has been tried, per the Python-capability-gap audit's own explicit correction of an earlier overclaim `[pce-017]`.

---

## 13. Explicit List of Claims the Evidence Would NOT Justify

Even a fully successful run of the design above would **not** justify claiming:

1. That FeralEcho "learns" in general — only that this one specific, narrowly-scoped mechanism does, under the tested conditions.
2. Sustained, open-ended growth over an unbounded horizon — this design tests 4 rounds, not indefinite accumulation (that would require a further, separately-designed longitudinal study, analogous to the still-unbuilt "E8" `[pce-008]`).
3. That the live, currently-deployed RiverBrain mechanism (as it operates today, unmodified) demonstrates genuine competence — only that it *could*, once Step 0/1 are applied; the unmodified system remains, per this mission's own evidence, an L2 mechanism with a non-independent feedback signal.
4. Generalization beyond the specific task families tested — the fixture evidence (`[pce-014]`'s Attack 3) gives direct, real reason to expect this mechanism may fail exactly this kind of generalization, and the design's own transfer test is built to catch that, not assume it away.
5. Anything about `task_type_classifier.py`, `self_edit_attempt_ledger.jsonl`, `echo_state.py` valence, `seam_engine.py`, `curiosity_engine.py`, memory retrieval, E5-mini, or RAOC — none of these are touched by this design, and none should be cited as corroborating evidence for a RiverBrain-specific result without their own, separately-designed experiments.
6. Reproduction, inheritance, instinct, or "a digital organism" for the Lizard-Tail transplant result, however clean — per the mission's own explicit instruction, this is a causal state-transfer experiment on a statistics dictionary, nothing more, unless future evidence specifically earns a stronger term.
7. That transplanted state is provably authentic against a hostile third party, absent the provenance-manifest extension recommended in §10/§12 item 8 — without it, the claim rests on the experimenter's own good-faith execution log, not an independently checkable artifact.
8. That any positive result here says anything about consciousness, sentience, or experience in a phenomenological sense — this entire investigation is scoped to functional, measurable competence, and the evidence vocabulary used throughout has no vocabulary for, and makes no claim about, that separate question.

---

## Methodology Note

This mission ran five parallel, independently-instructed investigator agents (no shared context, no fork of this session's own reasoning) covering: (1) the E5-mini/capability-ceiling audit lineage, (2) the recursive-learning-ground-truth and Python-capability-gap lineages, (3) the RiverBrain/task_type_classifier causal-audit lineage, (4) a fast relevance triage of ~70 self-model/epistemic-arbitration/provenance files plus a deep read of `shadow_model.py` and `provenance_check.py`, and (5) a live source-wiring trace of the remaining candidate pathways plus a full audit of the repository's current uncommitted diff. Their reports were cross-checked against each other (three independently converged on the identical RiverBrain evaluator-leakage finding via different methods) and against this session's own direct source verification (`[pce-032]`) before being synthesized here — no single agent's conclusion was taken as final without at least one independent corroboration or a direct re-check.

## Previous-Claim Reconciliation

- **Confirmed**: Mission 31's specific empirical claim (state mutation → ranking change) `[pce-001]`. **Narrowed**: the implicit "L3/VERIFIED closed loop" reading of that mission, which this investigation and its own later evidence (`[pce-031]`) do not support for the *live, connected* pathway.
- **Confirmed**: `shadow_model.py`'s L1 retirement `[pce-019]` — unchanged, no drift.
- **Confirmed**: RAOC's stalled-at-pilot status `[pce-027]` — matches `CLAUDE.md` exactly.
- **Corrected**: `CLAUDE.md` Finding 86's characterization of `preference_provenance/` as "frozen at P0.1, no experiment run yet" is imprecise — 56 real trials exist on disk `[pce-026]`. The result of those trials remains unreviewed and UNKNOWN; this is a precision correction, not a reversal.
- **Corrected/DISPROVEN**: E5-mini's own "G0: QUALIFIED" claims (both the original and the post-repair version) — independently reconciled and falsified twice `[pce-010]`. This was already self-disclosed within that lineage's own documents; recorded here for completeness, not newly discovered by this mission.
- **New, not previously in `CLAUDE.md`**: a direct measured failure of RiverBrain's learned score against an independent criterion, once deconfounded, in the live `select_best_fallback_candidate()` code path `[pce-031]` — this is real, current, uncommitted production code this mission found and verified via direct diff read, and it is the single most directly relevant piece of evidence against trusting the live mechanism's output as competence without the Step 0/1 fix proposed above.

## Independent Review

This mission changed no production code — it produced this report and its evidence ledger only. Per this skill's own Phase 9, `feral-independent-review` is **not required** to consider this mission complete, since no implementation shipped. It **is** strongly recommended before Step 1 (§7/§12) — a human-reviewed diff to a protected file — actually lands, and again before any run of the experiment is treated as decisive, given this project's own repeated history of first-draft overclaiming being caught only by a second, independent pass (`[pce-007]`, the E5-mini G0 sequence, the 2026-09-14/15 task-type behavioral-experiment correction chain).

## Integrity Record

```
production changes: NO
files changed: audits/2026-09-19_persistent_competence_experiment_design.md (new),
               audits/2026-09-19_persistent_competence_experiment_design_evidence_ledger.json (new)
Git HEAD before: 2fba42644c82b9f7096276f4dd338d615cf1bcce
Git HEAD after:  2fba42644c82b9f7096276f4dd338d615cf1bcce
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: none (5 parallel investigator subagents launched and completed; no FeralEcho/Ollama process touched)
configuration changes: NO
test changes: NO
temporary files created: /private/tmp/claude-501/.../scratchpad/scan_transcripts.py (unrelated prior task in this session, already disclosed at the time), /tmp/transcript_list.txt, /tmp/status_end.txt (this mission's own scratch)
temporary files cleaned: /tmp/transcript_list.txt and /tmp/status_end.txt left in place (outside the repo, harmless, standard scratch location; not referenced by anything else)
orphaned processes: checked, none found
known anomalies: none — working-tree porcelain status identical in content before and after (171 pre-existing modified/untracked entries, none newly touched by this mission except the two new audit files listed above)
known deviations from requested methodology: none — investigation-only throughout; no experiment from §7-9 was executed, per the mission's explicit "do not begin by implementing anything" instruction; the only commands run against the live system were read-only (grep, git status/diff/log, file reads) and five read-only research subagents
```
