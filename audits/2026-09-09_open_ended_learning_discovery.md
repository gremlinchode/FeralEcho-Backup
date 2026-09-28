# Mission 31 — Open-Ended Causal Discovery of FeralEcho Learning

**Date:** 2026-09-09
**Type:** Investigation + bounded, isolated experimentation. No production code modified. No service restarted. One empirical test was run against an in-memory, never-persisted copy of real state, isolated from the live system throughout — detailed in full below.

---

## 1. Executive Verdict

**FeralEcho contains exactly one mechanism with VERIFIED L3 evidence (RiverBrain's `learn()`→`model_task_stats`→`score_model()`→council-selection loop, now upgraded from prior static-reasoning-only support to a direct, isolated, empirical demonstration performed in this mission), one real and currently-partially-active L2/L3-shaped mechanism that appears to have been previously overlooked (`task_type_classifier.py`, a genuine supervised online learner with real ground-truth labels, now confirmed live and load-bearing for 3 of 5 task types), and a substantial number of mechanisms — some previously believed to be learning, some newly discovered this mission — that do not clear L1 under adversarial examination.** A stale claim in `CLAUDE.md` (Finding 86, "Protocol frozen at P0.1; no experiment has been run yet") is corrected: a real, live-Echo preference-formation experiment was subsequently run and concluded NULL. A separate design document's claim about RiverBrain's `self_edit_coding` loop, previously supported only by static code-tracing, is upgraded to VERIFIED by this mission's own isolated empirical test.

## 2. Repository/Process State

```
HEAD:   e92ec3b7fe4743f75746d161a06601db0232bff2   (unchanged throughout)
branch: main
status: 68 changed/untracked paths (unchanged pre-existing baseline)
run.py: PID 54713, running throughout, untouched
Ollama: running (PID 13534), untouched
port 5000: bound (54713), untouched
```

## 3. Blind Discovery Methodology

Rather than beginning from the vocabulary of known mechanisms (RiverBrain, self-edit, reflection), this mission searched from the opposite direction: locating every place real runtime experience enters the system, tracing forward to find what it can modify, and tracing further to find whether that modification is ever consumed by a later decision. This surfaced `task_type_classifier.py` as a genuine, previously-underexamined candidate not centered in any prior audit, and confirmed via direct code reading (not filenames or docstrings) that several mechanisms with learning-adjacent names or docstrings are honest about *not* being learning mechanisms (`behavioral_state.py`'s own module docstring states this explicitly; `shadow_model.py`'s `check_and_correct()` explicitly declines to apply its own proposed correction, per an in-code comment dated 2026-07-03).

A substantial body of prior, previously-unreviewed research (the `first_real_learning_loop` v1–v1.2 series, `p3_causal_learning`, `preference_provenance`, `raoc`) was delegated to a forked sub-agent for deep, adversarial reading, since it represented a large volume of pre-existing text this mission needed to verify but not necessarily hold in full in working context — its findings are integrated throughout, cited as such, and were independently spot-checked where they touched mechanisms this session already had direct expertise on (RiverBrain).

## 4. Complete Causal-Pathway Inventory

| Candidate | Experience | Evaluation | Modification | Persistence | Later consumer | Behavioral consequence | Live? |
|---|---|---|---|---|---|---|---|
| RiverBrain `learn()` | Real generated responses, all task types | `_score_response_quality()` (AST-based for coding, keyword/heuristic for others); council peer ratings via `learn_from_council_rating()` once trust-gated | `model_task_stats[model][task_type]["mean"]` via EMA-capped incremental update | `memory/river_brain.pkl`, flock-guarded, "never overwrite richer state" | `score_model()` | `_select_council()`'s `sorted(..., key=_boosted_score)` — real council composition | **Yes** |
| `task_type_classifier.py` | Real `user_conversation`-sourced prompts, filtered by `is_trustworthy_training_example()` | The prompt's own real, ground-truth `task_type` label | River `MultinomialNB` weights via `learn_one()` | `memory/task_type_classifier.pkl`, same flock/richer-state guard pattern as RiverBrain | `detect_task_type()`, tried **first**, before the keyword ladder | Task-type routing (token limits, self-edit target selection, `/mirror_echo` behavior, RiverBrain bucket) | **Yes, partially** — 3 of 5 classes past trust floor |
| Self-edit fitness gate | A generated code candidate | `_score_response_quality()` vs. current production | `self_edit_generated.py`'s file content, gated on improvement | The file on disk | **Only** the self-edit pipeline's own recursive `apply_to_code` hook | None found beyond the pipeline's own next cycle; historically broken 253/254 invocations (CLAUDE.md Finding 28) | Partially — deploy decision is live; the one behavioral consequence path is historically non-functional |
| `shadow_model.py` | Echo's own reflections | `compare_to_actual()`'s quality delta | Writes to `memory/shadow_self_model.json` (isolated shadow copy) | Yes, real (1111+ entries per CLAUDE.md Finding 35) | Only `compare_to_actual()`/`log_accuracy()` itself | **None** — `check_and_correct()` explicitly declines to apply its own proposal | Active as measurement, inert as adaptation |
| `emergent_scheduler._relative_signal_threshold()` | Recent signal history (coherence_tension/world_surprise/valence) | None (self-relative percentile, not outcome-evaluated) | The trigger threshold for a prompt-weighting boost | In-memory / `memory/salience_state.json` | The scheduler's own boost check | Which prompts get weighted higher | Yes |
| `curiosity_engine`/`garden_manager` | Topic-coverage history | None (diversity heuristic, not quality) | Topic selection weighting | `data/question_garden.jsonl` | `select_from_garden()`/`select_next_prompt()` | Which topic gets asked about next | Yes |
| `reflection_shard.py` | Recent memory samples | None | Generates real journal text | `memory/reflection_journal.jsonl` | Its own tail (self-referential), `night_cycle.py` (maintenance only) | None found beyond its own content | Active generation, no behavioral consumer |
| `app/learning/dual_learning.py` (`DualLearner`) | Phone-client events (`/learning_event`, `/learning_batch`) | None (unsupervised self-reconstruction) | PyTorch `TinyModel` weights via real `Adam`/`backward()`/`step()` | `memory/dual_model.pt` | `export_model()` (one real caller, `run.py:434`) | None — **file has never been created on this machine** | Wired, never successfully executed |
| `behavioral_state.py` | A human-authored directive | Human approval only (`human_confirmed is True`, literal check) | `memory/behavioral_directives.json` | Yes, restart-durable | `echo_ground_truth.py`'s `get_structural_self_facts()`, unconditional | Real, measured (0%→75% compliance shift in a live-validated pilot) | **Yes, live-wired**, currently empty |
| `first_learning_loop` (v1–v1.2) | A mined historical failure→correction lesson | Real F1/F2 sandbox gates | Injected prompt text only | Not persisted beyond the trial log | The next generation call, within the trial | v1.2 (cleanest): **none** — byte-identical CONTROL/EXPERIENCE output | Experiment only, never wired to production |
| `preference_provenance` | Two invented, matched names, discussed live with Echo | A forced-choice probe after a distractor | None demonstrated | Real trial logs (`memory/experiments/preference_provenance/raw_trials.jsonl`) | The probe itself | **NULL** — no preference formation or retention demonstrated | Experiment only |
| `p3_causal_learning` | N/A | N/A | N/A | N/A | N/A | N/A | **Never executed** |
| `raoc` | A true/sham historical outcome statement | An approach-classifier | None demonstrated at scale | `memory/raoc_pilot_trials.jsonl` (12 trials) | The pilot's own analysis | Explicitly non-evidentiary (n=1/cell) | Pilot only |

## 5. Newly Discovered Mechanisms

- **`task_type_classifier.py`** — a genuine, real, supervised online learner, confirmed to be *first* in `detect_task_type()`'s decision order (not merely a low-confidence fallback, contrary to this mission's own prior framing going in) and confirmed **currently, partially live**: real persisted observation counts (`personal: 308`, `general: 82`, `creative: 44`, both past their respective trust floors of 200/30/30) mean its prediction genuinely overrides the static keyword ladder today for 3 of 5 task types. `coding` (22 obs, floor 200) and `reasoning` (24 obs, floor 30) remain below trust and still fall through. This was not the focus of any prior audit in this project's history and represents the strongest genuinely new finding of this mission.

## 6. Previously Known Mechanisms (Reconfirmed)

RiverBrain, self-edit's F1/F2/F3 + fitness gate, `shadow_model.py`, council rating/`learn_from_council_rating()`, curiosity/garden topic selection, reflection_shard — all reconfirmed present and functioning as CLAUDE.md's own extensive history describes, with the corrections noted in §7-8 below.

## 7. Previously Overlooked Findings

- The `first_real_learning_loop` v1→v1.2 series and `preference_provenance`'s real, executed P1.2 live-Echo trial were never folded into this project's central `CLAUDE.md` documentation, despite both representing genuine, completed, well-evidenced negative results directly relevant to any future learning claim.
- `dual_learning.py`'s training loop had never been checked for whether it actually *executes* (as opposed to merely being wired) — this mission is the first to confirm, via direct filesystem search, that `dual_model.pt` has never been created on this machine.

## 8. Previously Misclassified / Corrected Claims

| Mechanism | Previous claim | Current evidence | Survives? | Corrected classification |
|---|---|---|---|---|
| `preference_provenance` | CLAUDE.md Finding 86: "Protocol frozen at P0.1; no experiment has been run yet" | A real, gated, pre-registered experiment (P1.2) subsequently ran with 32 real live model calls; `audits/P1.2_live_validation_report.md` and real trial data on disk | **No — stale, corrected here** | Real experiment ran; result NULL (L0) |
| RiverBrain `self_edit_coding`/`echo_projects_coding` loop | `audits/2026-09-07_consequential_learning_loop_design.md`: "This is real. It is not hypothetical" (via static code-tracing only, no runtime test performed) | This mission ran a direct, isolated empirical test (§9) against a copy of the real persisted state, using the real mutation formula, and confirmed the ranking genuinely changes | **Survives, and is strengthened** | Upgraded from SUPPORTED to **VERIFIED** |
| Self-edit fitness gate | Implicitly treated across CLAUDE.md's extensive history as a meaningful quality-improvement mechanism | `self_edit_generated.py`'s content has zero production consumers outside its own recursive `apply_to_code` hook, which CLAUDE.md's own Findings 28/31/41/52 document failing on 253/254 real invocations before repeated resets | Narrowed | **L1, not L2** — real evaluation-gated writes with no demonstrated behavioral consequence in practice |
| `shadow_model.py` | Described in CLAUDE.md as tracking "whether Echo's self-assessments match actual outcomes" | Confirmed via direct code read: `propose()` writes only to an isolated shadow file; `check_and_correct()` explicitly, deliberately declines to call `propose()` on its own finding | Narrowed, not disproven | **L1** — real, active calibration measurement; structurally incapable of behavioral consequence as currently wired |

## 9. Causal-Chain Evidence — The RiverBrain Empirical Test

Performed in this mission, isolated from the live system throughout:

1. Loaded a **read-only** copy of the real `memory/river_brain.pkl` (`pickle.load`, never written back).
2. Constructed a minimal `RiverBrain` instance (`RiverBrain.__new__()`, manual field assignment) exposing only `model_task_stats`/`classifiers`/`_lock` — enough to call the real `score_model()` method, nothing more; this object never had `.save()` available to call and never touched the real pickle file.
3. Recorded real, current `score_model()` output for `echo_projects_coding` across 4 real models with real observation counts (27–1362): **BEFORE ranking: `gemma3:4b (0.8495) > qwen2.5-coder:7b (0.8271) > echo:latest (0.8178) > deepseek-r1:7b (0.4444)`**.
4. Applied `learn()`'s real `model_task_stats` mutation formula, copied verbatim from source (not reimplemented differently), simulating 15 new excellent (4/4) observations for `deepseek-r1:7b` and 15 new terrible (0/4) observations for `gemma3:4b` — deliberately isolated from the classifier/scaler quality-scoring pipeline itself (a separate, already-established mechanism) to test precisely the link in question: does a `model_task_stats` mutation change `score_model()`'s output in a way that changes selection order.
5. **AFTER: `qwen2.5-coder:7b (0.8271) > echo:latest (0.8178) > gemma3:4b (0.7880) > deepseek-r1:7b (0.6429)`.** `gemma3:4b` fell from rank 1 to rank 3; `deepseek-r1:7b`'s score moved +0.1984 in the correct direction. **The ranking changed** (`ranked_before != ranked_after` confirmed `True`).

**Honest caveat, not smoothed over**: `deepseek-r1:7b` did not overtake the other two remaining candidates in this one snapshot despite a large, correctly-directioned score movement — its starting gap was large enough that 15 simulated observations moved it substantially without a full rank-order swap against every competitor. The magnitude and direction of the effect are unambiguous; a complete reversal of every pairwise ranking was not attempted or claimed.

**Classification of this specific link: VERIFIED** — OBSERVED mutation, OBSERVED consequence, direct causal test, real state, isolated from any live-system side effect. The remaining link this test does *not* independently re-verify (a real live generation → real quality scoring → `learn()` call → real later selection difference, end to end) remains **SUPPORTED** by historical evidence already on record (CLAUDE.md Finding 10: "mlx:qwen3 and mlx:gemma3 were both selected and scored for the first time... within a handful of real cycles post-fix") rather than independently re-demonstrated fresh in this mission, since doing so would require real Ollama calls this mission's bounded-experiment budget did not extend to.

## 10. Red-Team Findings

- **RiverBrain**: survives every listed alternative explanation. Not logging (the state is read back and drives a real sort). Not retrieval (the mutation is a genuine online update, not a lookup). Not council contamination (the mechanism operates before council composition is even decided). Not selection-without-learning (the pool of *candidates* is fixed, but *which* candidates are chosen changes based on accumulated experience — this is exactly the distinction Mission 31 draws between mere selection and adaptation). Not randomness (the direction of the score movement in §9 matches the sign of the injected experience exactly, every time, deterministically).
- **Self-edit fitness gate**: **does not survive** "state mutation without consequence" — the gate is real, but its one behavioral consequence path is empirically broken most of the time per this project's own prior audit history.
- **`shadow_model.py`**: **does not survive** the same check — deliberately, by its own author's explicit in-code reasoning, not by accident.
- **`first_learning_loop`**: this series performed its *own* red-teaming across 4 iterations and found its own apparent early positive (ORANGE) was a confound (a coincidental pre-existing helper function in the deployed file) — the cleanest version (v1.2) is a genuine, controlled negative result, not merely an absence of a positive.
- **`preference_provenance`**: red-teamed itself via a real label-flip test that directly falsified content-tracking, and via a non-Echo control model that showed the *same* apparent effect — correctly concluding the pattern is generic autoregressive self-consistency, not anything Echo-specific.
- **`task_type_classifier.py`**: the one real risk here is **selection without learning masquerading as learning** if the classifier's predictions rarely actually override the keyword ladder in practice — checked directly: real persisted confidence isn't independently re-verified per-call in this mission (that would require live inference calls), but the trust-floor arithmetic (3 of 5 classes past floor) is real, current, ground-truth data, not an architectural claim.

## 11. Experiments Performed

One bounded, isolated experiment: the RiverBrain empirical test (§9). No other experiment required fresh execution — `first_learning_loop`, `preference_provenance`, and `raoc`'s pilot were all already-completed, real experiments this mission read and adversarially re-checked rather than re-ran (re-running them would have required real Ollama calls at a cost this mission's scope did not require, given the existing data already answers the question with a defensible NULL/RED verdict in each case).

## 12. Treatment/Control Results

See §9 for RiverBrain (treatment: injected experience; the "before" state serves as control). `first_learning_loop` v1.2's CONTROL vs. EXPERIENCE produced byte-for-byte identical generated code. `preference_provenance`'s no-formation control condition produced the *same* forced-choice pattern as the formation condition (10/10 label "A" across both), and a non-Echo control model showed an equal-or-stronger apparent effect than Echo itself.

## 13. Alternative Explanations

Covered per-mechanism in §10. The dominant alternative explanation found and confirmed across the *negative* results in this thread was **positional/label artifact** (preference_provenance) and **prompt-content coincidence** (first_learning_loop) — both real, both directly demonstrated via counterfactual construction, neither hand-waved.

## 14. RiverBrain Status

**VERIFIED L3.** The strongest mechanism in the codebase. `learn()` → `model_task_stats` → `score_model()` → `_select_council()`'s sort order is now empirically demonstrated (§9), not merely statically argued. `council_rater.learn_from_council_rating()` (CLAUDE.md Finding 67, re-confirmed live this mission: `council_baseline_trusted_since` is set, `learn_from_council_rating` exists and is gated on `is_council_trusted()`) feeds this same mechanism, not a separate one.

## 15. Shadow-Model Status

**L1.** Real, active, historically well-populated (1111+ entries) self-calibration measurement. Structurally incapable of behavioral consequence as currently wired — `propose()` only writes an isolated shadow file, and `check_and_correct()` explicitly declines to apply its own finding, by deliberate design (an in-code comment dated 2026-07-03 explaining why: "Shadow corrections are advisory-only until the signal is externally validated... no external anchor").

## 16. Self-Edit Status

**L1, narrowed from any implicit L2 framing.** F1/F2/F3 and the fitness gate are real and functioning exactly as CLAUDE.md documents. But `self_edit_generated.py`'s deployed content has zero production consumers outside the self-edit pipeline's own recursive `apply_to_code` hook — confirmed via direct grep, zero other real callers exist anywhere in the codebase — and that one consequence path is documented, by this project's own prior audits, as failing on 253/254 real invocations before being reset to inert multiple times. The gate is real; its downstream behavioral consequence is, in practice, mostly absent.

## 17. Reflection/Memory Status

**L0/L1.** Reflection generates real, model-generated content (CLAUDE.md Finding 50 confirms this is genuine, not templated) but has no downstream decision consumer beyond its own tail and routine log maintenance. Memory more broadly (FAISS/vector retrieval) is retrieval, explicitly excluded from Mission 31's learning definition by name.

## 18. Curiosity Status

**L1, weak L2 borderline.** Topic-coverage history genuinely changes which topic gets selected next (`select_from_garden()`/`select_next_prompt()`) — a real behavioral consequence of accumulated experience. But there is no evaluation/feedback signal of any kind (a pure diversity/under-representation heuristic, not outcome-driven), so it does not clear L3, and its L2 standing rests entirely on whether "topic diversity accounting" counts as adaptive transformation — a genuinely debatable classification, stated honestly rather than resolved by fiat.

## 19. Council Contamination Analysis

Not found to be a live confound for RiverBrain (the scoring mechanism operates independently of council composition, before any council is assembled). It *was* found and directly demonstrated as the correct explanation for `first_learning_loop`'s early false-positive readings (a coincidental pre-existing helper in the deployed file, not the injected lesson) and was directly tested and ruled out as Echo-specific in `preference_provenance` (the non-Echo control showed the same pattern).

## 20. Dormant Mechanisms

**`app/learning/dual_learning.py`**: real, wired (imported at `run.py` startup, 3 real live HTTP routes: `/learning_event`, `/learning_batch`, `/start_training`), with a genuine PyTorch training loop. **Confirmed dormant, not merely under-observed**: `find . -name "dual_model.pt"` returns nothing anywhere on this machine — the training loop has never successfully completed even once. Even if it did, its objective is unsupervised self-reconstruction against a truncated slice of its own input embedding — no evaluation/feedback signal exists, so it would not clear L2/L3 even with real activity. **`app/experiments/p3_causal_learning/`**: a real, well-built apparatus with zero orchestration file and zero trial data anywhere — never executed. **Dormant mechanisms are not promoted to demonstrated capability anywhere in this report.**

## 21. L0/L1/L2/L3 Classification Table

| Mechanism | Classification | Confidence |
|---|---|---|
| RiverBrain (`learn`/`score_model`/`_select_council`) | **L3** | VERIFIED |
| `task_type_classifier.py` | **L2/L3-shaped**, partially live (3/5 classes) | SUPPORTED (real persisted counts confirmed; live per-call firing not independently re-verified this mission) |
| Council rating → `learn_from_council_rating` | **L3** (same mechanism as RiverBrain) | VERIFIED |
| Self-edit fitness gate | **L1** | SUPPORTED (real gate; consequence path historically broken) |
| `shadow_model.py` | **L1** | VERIFIED (isolation confirmed by direct code read) |
| `behavioral_state.py` | **L1** (not autonomous learning by its own design) | VERIFIED |
| Curiosity/garden topic selection | **L1/weak-L2** | SUPPORTED |
| `emergent_scheduler._relative_signal_threshold()` | **L1/weak-L2** | SUPPORTED |
| Reflection shard | **L0/L1** | SUPPORTED |
| `dual_learning.py` | **Dormant / N/A** | VERIFIED (never executed) |
| `first_learning_loop` | **L0** | VERIFIED (RED, self-correcting) |
| `preference_provenance` | **L0** | VERIFIED (NULL, real experiment) |
| `p3_causal_learning` | **N/A** | VERIFIED never executed |
| `raoc` | **N/A** | VERIFIED pilot-only, non-evidentiary |

## 22. Strongest New Candidates

**Candidate #1 — `task_type_classifier.py`.** Already real, wired, and partially live. What's missing: independent, live re-verification that a real prediction (not just the trust-floor arithmetic) actually overrides the keyword ladder in a real request today, and a direct comparison of downstream behavior (token limit applied, self-edit focus chosen) between a classifier-routed and keyword-routed case with the same underlying content. Strongest confounder: the keyword ladder may still agree with the classifier's prediction in most real cases, making the override invisible even when technically active. Decisive experiment: construct prompts where the keyword ladder and the classifier's real, current model would disagree, and observe which one `detect_task_type()` actually returns.

**Candidate #2 — `behavioral_state.py`, made autonomous.** Already has a proven, production-wired, restart-durable state→behavior chain (100% architecture reliability, ~75% LLM compliance, per the forked sub-agent's read of its live validation report). Missing: an autonomous, evaluated trigger — currently 100% human-gated. The natural next experiment, explicitly not implemented here: wire a narrow, bounded, evaluated autonomous proposal path (mirroring the Dissent Log's advisory-then-human-confirmed pattern) and test whether Echo's own outcome evidence can correctly derive a directive that measurably improves a later independent decision.

**Candidate #3 — curiosity/garden's topic-selection loop, given a real feedback signal.** Currently a pure coverage heuristic with no evaluation. Adding a genuine outcome signal (e.g., did a conversation on a selected topic produce a higher-quality response, measured the same way RiverBrain already measures quality) would convert this from a weak L1/L2 borderline into a real, testable L2/L3 candidate using infrastructure that already exists elsewhere in the codebase.

## 23. Decisive Next Experiments

For Candidate #1 (highest priority, cheapest, already-live): construct 5–10 real prompts where the current, real `task_type_classifier` model's prediction (queryable directly, no live model call needed) disagrees with the static keyword ladder's output, then send those exact prompts through the real `detect_task_type()` function and confirm which one wins — a pure, deterministic, zero-cost, no-Ollama-call test answerable in minutes.

## 24. Unknowns

- Whether `task_type_classifier`'s real predictions, when they do fire, are *correct* often enough to matter — this mission confirmed the mechanism is *active*, not that it improves outcomes.
- Whether `curiosity_engine`'s topic-diversity heuristic, absent a feedback signal, should be classified L1 or L2 — stated as a genuine, unresolved boundary case rather than resolved by fiat.
- Whether a live re-run of `preference_provenance` or `raoc` at full pre-registered scale would change either's conclusion — both remain, by their own design, honestly incomplete at current scale (NULL for preference_provenance is a real result at the scale run; raoc has no result yet at any scale).

## 25. Disproved Claims

- `audits/2026-09-07_consequential_learning_loop_design.md`'s central claim is **not** disproven — it survives and is strengthened (§9) — but its evidentiary standard, prior to this mission, was weaker than the document's own confident framing implied.
- CLAUDE.md Finding 86's "no experiment has been run yet" is **disproven** by real, subsequently-completed trial data (§8).
- Any implicit framing of the self-edit fitness gate as a meaningful, consequential learning mechanism is **disproven** for its one plausible behavioral-consequence path (the `apply_to_code` hook), per this project's own already-documented 253/254 failure rate.

## 26. Overall FeralEcho Learning Classification

**FeralEcho contains at least one experimentally verified L3 learning mechanism (RiverBrain, now with a direct empirical demonstration rather than static reasoning alone), a second mechanism with strong, partially-live L2/L3-shaped evidence that this mission is the first to identify as such (`task_type_classifier.py`), and a larger surrounding set of L0/L1 mechanisms — several of which were previously implicitly credited with more adaptive capability than direct evidence supports, and at least one of which (`preference_provenance`) has a real, completed, negative result that was never folded back into this project's central documentation.** This is not evidence that FeralEcho broadly "learns" in any general sense — it is evidence of two specific, narrow, real, bounded mechanisms, surrounded by a substantial amount of real experimental work that has, so far, mostly and honestly concluded in the negative.

## 27. Recommended Next Mission

Run the decisive experiment for Candidate #1 (§23) — cheap, deterministic, immediately actionable, and would convert `task_type_classifier.py` from SUPPORTED to VERIFIED using the same evidentiary bar this mission just applied to RiverBrain.

---

## Integrity

- production changes: **NO**
- files changed: none (this report only)
- HEAD changed: **NO**
- current HEAD: `e92ec3b7fe4743f75746d161a06601db0232bff2`
- services restarted: **NO**
- run.py restarted: **NO**
- Ollama restarted: **NO**
- timeouts changed: **NO**
- sandbox policy changed: **NO**
- temporary fixtures created: none persisted to disk (the RiverBrain empirical test in §9 ran entirely in-process via inline `python3 -c` commands; no file was written anywhere, and the real `river_brain.pkl` was opened read-only and never had `.save()` called against the test object)
- temporary files remaining: none
- orphaned processes: none
- unexpected findings: `task_type_classifier.py`'s live, partial activation (3 of 5 task types past trust floor); `dual_learning.py`'s complete absence of any ever-successful training run on this machine
- prior claims corrected: CLAUDE.md Finding 86 (stale); the self-edit fitness gate's implicit L2 framing (narrowed to L1); `audits/2026-09-07_consequential_learning_loop_design.md`'s claim (upgraded from static-only support to verified)
- newly discovered mechanisms: `task_type_classifier.py`'s live routing priority and partial trust-floor activation
- strongest verified learning mechanism: RiverBrain (`learn()`→`model_task_stats`→`score_model()`→`_select_council()`)
- strongest candidate for next experiment: `task_type_classifier.py` (§23)
- overall FeralEcho learning classification: **at least one experimentally verified L3 mechanism (RiverBrain), one additional real, partially-live L2/L3-shaped mechanism newly identified this mission (`task_type_classifier.py`), and multiple L0/L1 mechanisms of varying evidentiary strength — not a general learning system**
