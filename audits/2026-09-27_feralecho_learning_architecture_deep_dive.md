# FeralEcho Learning Architecture: Full-System Deep Dive

**Read-only investigation and design. No model calls, no code changes, no production
modifications, no migration begun.** Builds directly on, and does not contradict,
`audits/2026-09-27_learning_investigation_synthesis.md` — this document goes further:
it traces the full system end-to-end, tests the single-root-cause hypothesis rigorously
rather than accepting it, and produces a complete, implementable architecture rather than
three parallel options.

---

## 1. Executive verdict

**Yes, this was becoming nickel-and-diming, but not because the individual probes were
wrong — because the probes had already answered the representation question and the
project was at risk of running a fourth variant of the same test.** The correct response
is not another micro-probe; it is committing to a specific, fully-specified architecture
built on the one principle this whole research arc has already validated:
**bounded, grounded, non-verbal representations with an explicit consumer work; asking a
frozen model to invent its own representation of what it learned, in natural language,
does not.** But that single hypothesis, tested rigorously rather than assumed, does
**not** explain all of the observed failures — `persistent_routing`'s null result used
exactly this "correct" substrate and still failed, for a second, independent, and more
mundane reason (task/feature degeneracy, insufficient exploration volume). The
recommended architecture must solve both problems, not just the more dramatic one.

---

## 2. Definition of genuine accumulated competence (adopted, not restated loosely)

Experience at T1 → an acquired, retained change → improved capability at T2, attributable
specifically to that retained change (proven by removal/substitution) → generalizing
beyond the originating instance → surviving a genuine restart → and, ideally, making
acquisition at T3 measurably easier or better. This is the controlling objective for
every design choice below.

---

## 3. Full empirical evidence ledger (extends the prior synthesis's table)

| Mechanism | Intended learning | What actually changed | Consumer | Causal evidence | Transfer | Restart | Accumulation | Verdict |
|---|---|---|---|---|---|---|---|---|
| RiverBrain `model_task_stats` | Which model/strategy performs best per task type | A real running mean, per (model, task_type), from real verified outcomes | `execute_self_edit()`'s fitness gate; `choose_model()`'s exploration signal | Direct: `attempt_ledger_test` shows the pickle hash is byte-identical on rejection, changed on acceptance | Within-bucket only (task_type granularity) | Yes — a pickle file, months of real production accumulation | Yes — observation counts climb continuously in real production | **DEMONSTRATED** |
| Council-rating→RiverBrain blend (Finding 67) | Fold peer-rating signal into the same substrate | Same mechanism, trust-gated additional input | Same consumers | Same kind of evidence, narrower | Same | Yes | Yes | **DEMONSTRATED, narrow** |
| VECT's real P | Autonomous lesson extraction | A real measured P-vs-Z advantage | Fresh prompt insertion | Real, mechanistically traced (`restart_persistence_transfer`) | Limited — 4 fixed code bodies, fixed in the restart follow-up | Yes, proven with distinct PIDs | Not attempted | **PARTIALLY DEMONSTRATED** (persistence: yes; autonomous acquisition: no — investigator-authored) |
| `persistent_routing` selector | Route among 3 prompt strategies by learned per-bucket mean | Real state change (S0≠S1, hashed) in 3/3 lineages | Holdout `select()` calls | None found — 0/12 holdout decisions changed | N/A — no effect to transfer | Tested via S0-substitution; no difference to attribute | N/A | **FALSIFIED**, root-caused precisely (§6) |
| `strategy_characterization` | Characterize whether 3 strategies differ at all | Real Friedman/Wilcoxon statistics computed | N/A — measurement only | N/A | N/A | N/A | N/A | **NOT ESTABLISHED (honest Outcome E)** |
| G3 micro-probe | Autonomous candidate-correction inference from diagnostic evidence | 7 real, logged candidate texts | None — feasibility probe only | Mechanically tested: 0/7 corrections passed the oracle | N/A | N/A | N/A | **FALSIFIED** |
| Belief-revision probe | Falsification-driven hypothesis revision | 3 real revision records | None | 0/3 materially different, testable H2 | N/A | N/A | N/A | **FALSIFIED** |
| `first_learning_loop` | Automated (non-LLM) lesson mining + transfer | Real, mechanically-verified NameError/retry pattern extraction | A fixed sentence template inserted into a fresh prompt | Weak — one inspected transfer pair shows byte-identical generated code across conditions | Not established | Not tested | Not attempted | **NOT ESTABLISHED** |
| `architecture_a_hot_stove_proof` | Failure-derived retry diagnostic on production self-edit path | Real diagnostic injected | Retry prompt | 5/6 vs 5/6 — no advantage | N/A | N/A | N/A | **FALSIFIED** |
| `retrieval_capacity_proof` / `minimal_relevance_gate` | Test whether richer memory representations help retrieval | Synthetic representations only (X4 explicitly labeled non-real) | A real relevance-gate feature set | Real: even the richest synthetic representation is correctly judged `NOT_RELEVANT` against a distant query | N/A | N/A | N/A | **APPARATUS/MEASUREMENT ONLY** |
| `provenance_f2_verification` | Test whether trace_id↔F2-outcome joins would work | N/A | N/A | **0 real joinable pairs exist in production today** | N/A | N/A | N/A | **NOT ESTABLISHED (plumbing incomplete)** |
| FAISS / vector memory retrieval (production) | Contextual recall | Real retrieval happens constantly | Prompt context only | Per Finding 75's own physiology audit (already independently verified): retrieval **never** touches model selection, task-type classification, or self-edit targeting — only two scheduling branches and one dedup gate | N/A | Yes (disk-backed) | No — retrieval doesn't compound | **DEMONSTRATED as retrieval, NOT as learning** |
| `self_model.json` / Liveness Ledger | Self-report grounding | Real, ground-truth-checked self-report fields | `echo_ground_truth.py`'s prompt slices | Real (Liveness Ledger checks these against fresh ground truth every cycle) | N/A | Yes | No | **DEMONSTRATED as monitoring, NOT as learning** |
| `task_type_classifier` (online BoW+NB) | Improve task-type routing from trustworthy examples | Real, trust-filtered online updates | `detect_task_type()`'s fallback path | Ground-truth checked by its own Liveness check | Within its own classification task only | Yes | Marginal (a classifier, not compounding skill) | **DEMONSTRATED, narrow, non-verbal** — same family as RiverBrain |

---

## 4. End-to-end current architecture map (producer → consumer traces)

- **Self-edit pipeline**: `plan_code_logic()` → `generate_code_from_plan()` → F1 (static
  scan) → F2 (kernel sandbox + `apply_to_code` smoke test) → F3 (post-write scan) →
  `execute_self_edit()`'s fitness gate (real RiverBrain-scored comparison, Finding 19) →
  `save_code()`. **This is the one full producer-to-consumer chain in the whole codebase
  with a real, demonstrated behavioral consequence** (candidates are genuinely rejected).
- **Council deliberation**: `river_deliberation._select_council()` reads RiverBrain's
  `model_task_stats` for ranking + exploration; `learn()` writes back after every real
  cycle. A real, closed loop — the second full chain.
- **Global Workspace / salience**: real publishers (`world_model.surprise`,
  `dream.synthesis`, `emergent_loop.salience`) → real consumers
  (`memory_bridge.set_workspace_bias()`, `river_deliberation.set_cached_world_surprise()`,
  curiosity topic bias) — a real, demonstrated **behavior-modulating** loop, but tuning
  *cadence and exploration bias*, not accumulating *skill*.
- **Dead/weak wires, identified directly**: `coupling_estimate` (computed, self-reported,
  zero real consumer until Phase 5's self-report slice — still not causally consequential);
  `wolf_friction_bridge` (deliberately dry-run only, by design, not a gap); RiverBrain's
  `self_edit_coding`/`echo_projects_coding` buckets cluster suspiciously tightly across
  very different real models (Finding 75/91's own finding) — plausibly a scoring-instrument
  ceiling effect, meaning that specific slice of RiverBrain may be *measuring* less than it
  appears to.
- **Duplicated/conflicting learning mechanisms**: `shadow_model.py` (retired, below-chance
  accuracy, correctly disconnected) attempted a *second*, independent self-assessment
  mechanism parallel to RiverBrain's grounded stats — a real historical instance of
  redundant architecture that was correctly killed once evidence came in. This is a
  precedent worth citing directly: **the project has already, once, correctly retired a
  duplicated learning mechanism on hard evidence** — the discipline this mission asks for
  has already been exercised successfully once.

---

## 5. Root-cause analysis — the single-hypothesis test, done rigorously

**The mission's proposed root cause**: *"FeralEcho repeatedly asks a frozen generative
model to invent the representation of what should be learned, while downstream machinery
lacks a mechanically grounded definition of what that representation means."*

**Tested directly against every failure in the ledger:**

| Failure | Does the hypothesis explain it? |
|---|---|
| VECT's autonomous-acquisition gap | **Yes, cleanly** — the representation (P's text) was never actually derived by any mechanism; the hypothesis correctly predicts this would be unreliable if attempted. |
| G3 (0/7) | **Yes, cleanly** — the model was asked to invent the representation (a causal hypothesis) in natural language; it did, confidently and wrongly, every time. |
| Belief-revision (0/3) | **Yes, cleanly** — same invented-representation problem, one step later in the loop. |
| `first_learning_loop`'s weak transfer | **Partially** — here the representation was *not* invented by the model (it's a fixed, mechanically-filled template) — yet transfer was still weak. This is evidence the hypothesis is **necessary but not sufficient**: removing the invention step alone didn't produce strong transfer, because the *template itself* was too generic/coarse to constitute a real, differentiating representation. |
| `persistent_routing`'s 3/3 null | **No — this is the critical counter-example.** The representation here was never invented by a model at all — it was a plain numeric lookup table, RiverBrain-shaped, exactly the substrate that works elsewhere. The failure here is a **second, independent root cause**: the feature space was too coarse to distinguish holdout tasks from the default bucket, and only 2 of 18 real prospective decisions ever produced a genuine multi-candidate comparison (per this session's own adversarial postmortem). This is a **design/statistical-power problem**, not a representation-invention problem. |
| `architecture_a_hot_stove_proof`'s null | **Ambiguous** — a diagnostic was injected, but into a retry *prompt*, asking the same frozen model to use it; closer to the G3 family than to persistent_routing's family. |

**Conclusion: the mission's hypothesis is correct but incomplete.** There are **two
independent root causes**, ranked:

1. **(Primary, most damaging) Representation-invention failure**: asking a frozen 7B
   local model to invent, in natural language, the specific content of what it should
   learn from one example, reliably fails — confirmed directly and repeatedly (G3,
   belief-revision), and consistent with VECT's own gap.
2. **(Secondary, but real, and easy to silently re-commit) Task/feature/exploration
   degeneracy, even under a correct, non-verbal substrate**: `persistent_routing` proves
   that choosing the right *kind* of representation (numeric, RiverBrain-shaped) is
   necessary but not sufficient — the *task design* feeding it also has to provide real
   variance and real exploration volume, or the mechanism never gets the chance to
   diverge from a default. **Any replacement architecture must solve both, or it will
   reproduce `persistent_routing`'s exact failure while believing it has fixed the
   representation problem.**

---

## 6. Why the demonstrated mechanisms worked, precisely

RiverBrain and `task_type_classifier` share four properties, independently verifiable
against source: **(a) bounded representation** — a fixed-shape running mean/classifier,
not an open-ended natural-language object; **(b) grounded update** — every update is
gated by a real, independently-computed outcome (oracle grade, quality scorer), never a
model's own self-report; **(c) an explicit, pre-wired consumer** — the fitness gate and
`choose_model()` read this state on every real cycle, not "eventually, if something
retrieves it"; **(d) real, high-volume, continuously-varying real-world exercise** —
tens of thousands of real observations per bucket, not a handful of designed episodes.
`persistent_routing` had (a), (b), and (c) — it lacked (d) at the scale actually needed,
and its *feature representation itself* (§5) further starved it of variance even within
its small budget.

## 7. Why the failed mechanisms failed, precisely

VECT/G3/belief-revision share the inverse of property (a): an **unbounded, self-invented
representation** (natural language), which removes the very thing that made RiverBrain
tractable — there's no fixed shape to update incrementally, no way to average across many
observations, and no way to grade a candidate's *content* independent of a full,
expensive verbal correctness check performed by the very same unreliable process.

## 8. Architectural principles derived from evidence (frozen, before design)

1. **Never require the acting model to invent the representation of what it learned.**
2. **A representation only counts as "grounded" if its update rule is a pure function of
   an independently-computed, oracle-verified outcome** — never a model's own confidence
   or self-report.
3. **Every acquired artifact must have a pre-wired consumer specified before the artifact
   is built**, not "stored for later."
4. **Task/feature design must be checked for real variance and real exploration
   opportunity *before* trusting a null result** — `persistent_routing`'s own
   after-the-fact discovery (2/18 genuine comparisons) should have been checked *before*
   running, and must be checked before running anything new.
5. **Search-and-verify, not verbalize-and-trust, is the correct way to let a frozen model
   contribute variation** — it only has to *generate candidates*, never *correctly
   diagnose why one is better*; the independent oracle does the diagnosing.

---

## 9–14. Substrate evaluations

**Verifier-guided search / skill acquisition**: directly avoids the verbalization
bottleneck (principle 1) by construction — the model never has to say *why* a candidate
works, only produce one. Doppelgängers attacked: *more inference compute* — real risk,
must be measured against a matched-compute CONTROL (the exact test this document's §29
proposes); *memorizing instance solutions* — mitigated only by a genuine held-out
generalization gate, which no experiment in this arc has yet successfully exercised
(named honestly as unresolved); *prompt engineering explaining it all* — the same
unresolved doppelganger flagged in the prior synthesis, carried forward as the
single most important gap.

**RiverBrain-extension**: the clear, proven, near-zero-marginal-cost floor for anything
new — model selection, tool selection, verifier reliability, confidence calibration are
all structurally identical to what RiverBrain already tracks (a scalar or small vector,
keyed by a bounded feature, updated by a grounded outcome). **Ceiling**: RiverBrain can
tell you *which* known option performed best; it cannot *generate a new option* — it is
a **SELECTION** mechanism, not a **VARIATION** mechanism. This is precisely why it cannot,
alone, be "the" learning architecture — it needs to be paired with something that
proposes new candidates.

**Trainable local learner (LoRA/QLoRA/adapters)**: feasible in principle on M5-class
unified memory for small (1–3B) models; genuinely new risk categories this codebase has
never managed (catastrophic forgetting, adapter rollback, training/eval contamination).
**Not recommended as the first move** — it solves a harder problem than the one actually
diagnosed (§5's root cause #1 is about *representation*, not about *weight plasticity*;
search-and-verify already gives the frozen model a way to contribute variation without
needing its weights to change at all).

**Hybrid search→consolidation**: the strongest long-run design — expensive search early,
consolidating into cheaper, reusable retained skills over time, optionally feeding a
trainable small model later once the skill library itself proves it generates real,
non-instance-specific signal. This is the recommended architecture (§15).

---

## 15. Recommended architecture — the **Verified Skill Ledger**

**One sentence**: a bounded, RiverBrain-shaped statistical substrate (SELECTION) paired
with a search-and-verify loop (VARIATION) that produces executable, oracle-graded
artifacts (never verbalized lessons) keyed by pre-declared, non-post-hoc mechanical
features of the task — with the exact same replay/substitution and restart-evidence
machinery this arc already built and proved, reused verbatim.

### 16. Component / data-flow diagram

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Task/world  │─────▶│  VARIATION        │─────▶│  Independent     │
│  generator   │      │  (frozen local     │      │  oracle          │
│  (existing:  │      │  model proposes    │      │  (existing:      │
│  tasks_v2,   │      │  N candidates,     │      │  oracle_runner,  │
│  worlds.py)  │      │  no verbal theory  │      │  sandbox.py)     │
└─────────────┘      │  required)         │      └────────┬─────────┘
                       └──────────────────┘               │ pass/fail
                                                            ▼
                                            ┌───────────────────────────┐
                                            │  SKILL LEDGER (new)        │
                                            │  keyed by pre-declared     │
                                            │  mechanical feature        │
                                            │  (never post-hoc)          │
                                            │  stores: executable code,  │
                                            │  provenance, held-out      │
                                            │  test record, hash chain   │
                                            └──────────┬────────────────┘
                                                        │ consult on lookup
                                                        ▼
                                            ┌───────────────────────────┐
                                            │  RiverBrain-shaped         │
                                            │  SELECTION layer           │
                                            │  (existing model_task_stats│
                                            │  shape, extended with a    │
                                            │  per-skill success rate)   │
                                            └──────────┬────────────────┘
                                                        │ consumed by
                                                        ▼
                                    execute_self_edit()'s fitness gate /
                                    a new skill-lookup consumer at
                                    generation time
```

### 17. Persistent state and schemas

- `skill_ledger/<feature_key>.json`: `{feature_key, code, code_hash, provenance:
  {source_failure_id, candidate_generation_log_ref, oracle_verdict, held_out_verdict},
  created_at, last_validated_at, success_count, failure_count}` — the same
  hash-then-freeze convention as `persistent_routing`'s `Selector.save()` and
  `freeze_procedure.py`, reused verbatim.
- `skill_stats.pkl`: a RiverBrain-shaped extension — `{feature_key: {"count": n, "mean":
  x}}` — literally the same data shape RiverBrain already uses, just keyed by skill
  rather than (model, task_type).

### 18. Update rules

A skill's `success_count`/`failure_count` update on every real *reuse* attempt (not just
its original creation), using the exact same incremental-mean formula RiverBrain already
implements — **no new update mathematics needs to be invented.**

### 19. Consumer rules — explicit, per Part VII's own requirement

- **Who reads the Skill Ledger?** A new, narrow lookup function at generation time:
  given a task's pre-declared mechanical feature, check for an existing validated skill.
- **When?** Before generation, not after — this is a routing decision, structurally
  identical to `persistent_routing`'s own `select()` call, just keyed by task feature
  instead of arbitrary strategy choice.
- **Why?** To skip search entirely when a validated skill already exists for this exact
  feature — the actual accumulation mechanism (§22).
- **How does it alter behavior?** It replaces "generate N candidates and search" with
  "apply the retained skill directly," a real, measurable reduction in search cost — the
  accumulation metric this document recommends (§22).

### 20. Generalization mechanism

A skill generalizes exactly as far as its feature key does. This is checked, not
assumed: after a skill is created, it must pass a **held-out validation gate** —
structurally identical to `strategy_characterization`'s own (never-triggered) Stage 2 and
VECT's own (initially-broken, later-fixed) TRAIN/HELD-OUT split — using fresh task/world
draws sharing only the feature key, confirmed disjoint via the exact token-overlap check
already proven in this codebase three times.

### 21. Forgetting / conflict / rollback

Forgetting: a skill whose recent reuse success rate (last-20 window, mirroring
`liveness_ledger.py`'s own already-proven recent-window pattern for exactly this kind of
staleness detection) drops below a threshold is flagged for review, not silently kept
forever. Conflict: two skills sharing a feature key cannot coexist — the ledger enforces
one skill per key, replaced only via a fresh held-out validation beating the incumbent
(the same fitness-gate logic Finding 19 already implements for self-edit). Rollback:
every skill file is hash-verified before use, exactly like `persistent_routing`'s
`R+`/`R-` recovery pattern — a corrupted or hash-mismatched skill is refused, not
silently trusted.

### 22. Accumulation mechanism, with a specified metric

**Recommended metric: reduced search cost for previously-unseen instances of an
already-solved feature key** (fewer candidates needed, or zero — a direct skill-ledger
hit). This is directly measurable, doesn't require claiming a vague "smarter" Echo, and
is the one metric this whole research arc has never actually tried to track. Skill N
enabling skill N+1: if a later, more complex task's own search step can *call* an earlier
retained skill as a sub-routine (not just imitate it), that's a real, checkable
compositionality claim — flagged here as the second-stage goal, not claimed as already
solved.

### 23. Hardware feasibility

Entirely M5-feasible: the search step reuses the same local Ollama inference already
running; the ledger is flat JSON files; no new training infrastructure, no GPU
requirement beyond what's already used. The Intel machine ("Ark/Air") could run a
second, independent skill-ledger accumulation in parallel for later cross-machine
comparison — not required for the first version. No external frontier-model dependency
in the learning loop itself, matching the mission's own explicit preference.

---

## 24. KEEP / MODIFY / RETIRE map

- **KEEP, unmodified**: `oracle_runner.grade()`/`sandbox.run_candidate()`, `replay.py`'s
  substitution design, the restart-evidence standard, RiverBrain's core update math, the
  hash-then-freeze provenance convention, the pre-registration/adversarial-review
  discipline itself.
- **MODIFY**: RiverBrain — extend (additively, per Finding 35's own established
  precedent) with a skill-keyed bucket, never touching existing (model, task_type)
  buckets.
- **RETIRE (as a *learning* mechanism, not as infrastructure)**: verbal single-shot
  candidate-inference-as-a-prerequisite (G3's own shape) and verbal belief-revision as
  tested — both stay documented, both stay available as *diagnostic* tools (they're
  useful for characterizing failures, per the forensic-mining pass's own real value), but
  neither is load-bearing for any future acquisition claim.
- **QUARANTINE FOR RESEARCH ONLY**: `first_learning_loop`'s fixed-template mechanism —
  its mining half is real and reusable (feeds candidate feature-key extraction); its
  template-filling half should not be extended further until the Skill Ledger's own
  variation step is proven, per the STOP list already established in the prior synthesis.

## 25. Migration plan — staged, falsifiable gates

- **Stage 0**: freeze this document and the prior synthesis as the baseline; no code
  touched yet (already satisfied by this mission's own constraints).
- **Stage 1 (minimal learning kernel)**: build the Skill Ledger schema + lookup function
  + RiverBrain-shaped stats extension, with zero real skills in it yet — pure
  plumbing, testable by unit tests alone.
- **Stage 2 (demonstrate acquisition)**: run search-and-verify on one real, already-
  characterized bug family (EP-A); gate: at least one genuinely held-out-validated skill
  is created. **Failure here stops escalation** — if search-and-verify can't even
  produce one validated skill on a family this well-characterized, the whole architecture
  needs rethinking before Stage 3.
- **Stage 3 (restart persistence)**: reuse `restart_persistence_transfer`'s exact
  distinct-process design, applied to the one skill from Stage 2. Gate: hash-verified
  recovery in a fresh process.
- **Stage 4 (transfer)**: fresh, disjoint held-out instances of the same feature key.
  Gate: measurable pass-rate improvement over a no-skill control, matching the discipline
  already proven in `restart_persistence_transfer`'s own statistical reporting.
- **Stage 5 (causal dependence)**: reuse `replay.py`'s exact substitution pattern — same
  starting state, skill removed vs. present. Gate: the advantage disappears when removed.
- **Stage 6 (accumulation)**: only after Stage 5 passes — attempt a second, different
  feature key, and check whether the ledger's own infrastructure (not the model) makes
  this second acquisition cheaper to validate. Gate: measurable, per §22's own metric.

## 26. Implementation blueprint

- **New package**: `app/experiments/skill_ledger/` (or, once past experimental status,
  `app/core/skill_ledger.py` + `memory/skill_ledger/`), mirroring every prior experiment
  package's own structure (`common.py`, `tasks.py` reused from
  `accumulation_probe`/`strategy_characterization` verbatim, `ledger.py`,
  `harness.py`).
- **Reused verbatim**: `oracle_runner.py`, `replay.py`'s substitution logic (generalized
  from selector-state to skill-file substitution), the `write_json_new`/hash-chain
  helpers already duplicated across every experiment package.
- **Not reused**: `persistent_routing/selector.py`'s specific epsilon-greedy strategy
  logic (a SELECTION-only mechanism with no VARIATION step) — the Skill Ledger needs a
  genuine search/candidate-generation step `persistent_routing` never had.
- **Tests**: a `verify_skill_ledger.py` script matching this project's own
  `verify_replay.py`/`verify_seam_engine.py` convention — synthetic discrimination cases
  before any real skill is trusted.
- **Rollback points**: every stage above is its own git-committable checkpoint; no stage
  begins before the prior stage's gate is independently confirmed.

---

## 27–28. Red-team attack, and the revised architecture

**Attacks attempted against the Verified Skill Ledger:**

- *"Merely sophisticated retrieval."* Partially true and conceded: at its core, this
  *is* retrieval — of a validated executable artifact rather than a verbal claim. The
  distinction that matters is the **validation gate before storage** and the **causal
  substitution test after** — retrieval alone (as `retrieval_capacity_proof` already
  showed) doesn't imply causal use; this architecture specifically adds the two links
  (validated storage, proven causal consumption) that plain retrieval lacks.
- *"Brute-force search, not learning."* A fair characterization of Stage 2 in isolation.
  It only becomes learning at Stage 6 — if and only if the ledger measurably reduces
  future search cost. **This must not be assumed; §29 makes it the actual kill test.**
- *"Retained skills are instance-specific."* The single most serious, still-unresolved
  risk — carried forward from the prior synthesis, not newly solved here. The held-out
  gate (§20) is the only defense, and it has never once been successfully exercised in
  this codebase (Stage 2 never fired anywhere it was tried). **This is a real, named
  weakness, not a solved problem.**
- *"Base-model capability explains any observed improvement."* Directly testable — and
  is exactly §29's proposed kill test.
- *"Verifier leaks answers."* Low risk — `oracle_runner.grade()` has been independently
  hardened across six+ prior experiments in this exact codebase; still must be
  re-confirmed for this specific reuse, not assumed transferred.
- *"Accumulation won't occur."* Honestly acknowledged as unproven — §22's metric is
  specified precisely so this claim is falsifiable rather than rhetorical, and Stage 6 is
  explicitly gated on it, not assumed.

**Revision made after this attack**: the architecture as first sketched treated Stage 2's
"one validated skill" as sufficient to proceed. **Revised**: Stage 2's gate now requires
the skill to pass the held-out check *and* to be compared against a matched-compute,
best-effort CONTROL prompt (no search) on the same held-out instances — closing the
"base model already explains it" doppelganger at the earliest possible stage instead of
deferring it to a later, more expensive step.

## 29. Cheapest architectural kill test (not executed here)

**Design (not run)**: one already-characterized real bug family (EP-A, the tag-priority
inversion — chosen because its real mechanism is already known precisely, letting success
be graded against ground truth, not just pass/fail). Two matched-compute conditions on
the same set of fresh, disjoint instances: (a) a single, best-effort engineered prompt,
zero search; (b) a small search-and-verify loop (e.g., 5 candidates, oracle-filtered),
*without* yet building any ledger/persistence machinery at all. **If (a) matches (b)'s
pass rate, the entire Verified Skill Ledger architecture is likely misguided** — the
"variation" step would be adding nothing beyond what better prompting already gets for
free, and the far larger investment in ledger/persistence/consolidation machinery would
not be justified. This is answerable at a call budget comparable to the G3/belief-revision
probes already run this session (single-digit to low-double-digit real calls) — **cheap,
fast, and a genuine go/no-go gate**, not a rhetorical formality.

## 30. Exact next action

Run §29's kill test — nothing else — before writing a single line of Skill Ledger code.

---

## Final questions, answered directly

1. **Are Gremlin and ChatGPT nickel-and-diming?** Yes, in the specific sense that the
   representation question had already been answered by G3/belief-revision and running a
   fourth verbal-substrate variant would not have added new information — but the
   individual probes themselves were correctly designed and genuinely necessary to reach
   that conclusion with confidence; the mistake would have been in what came *next*, not
   in what already happened.
2. **The architectural problem, precisely**: two independent root causes — (a) requiring
   a frozen model to invent its own learning representation in natural language, and (b)
   even when avoiding (a), under-provisioning task/feature variance and exploration
   volume (persistent_routing's own mistake) — both must be solved, not just the more
   visible one.
3. **What should replace the current approach**: the Verified Skill Ledger — a
   RiverBrain-shaped, non-verbal, grounded SELECTION layer paired with a genuine
   search-and-verify VARIATION step, producing executable artifacts, never verbalized
   lessons.
4. **What Echo actually needs to change internally when it learns**: a bounded numeric
   record (a skill's success statistics) and, separately, an executable artifact file —
   never a natural-language belief that some downstream process is trusted to correctly
   interpret and re-derive later.
5. **Can this be done without changing model weights?** Yes — this is the entire point of
   routing variation through search-and-verify rather than through inference reliability;
   the frozen model only needs to *propose*, never to *correctly explain*.
6. **Should weights eventually change?** Possibly, as a later-stage consolidation step
   (distilling a mature, validated skill library into a small trainable model) — but only
   after the Skill Ledger itself proves out through Stage 6, not before, and not as the
   first move.
7. **Role for natural-language reflection, if any**: diagnostic and human-facing only —
   useful for *characterizing* a failure for a human/Claude audience (exactly what the
   forensic-mining pass already demonstrated is valuable), never load-bearing for the
   acquisition mechanism itself.
8. **The actual consumer of acquired competence**: a pre-wired lookup at generation time,
   keyed by a pre-declared mechanical task feature — specified in the architecture before
   a single skill is created, per Part VII's own requirement.
9. **How competence N enables N+1**: directly, if a later task's search step can invoke
   an earlier validated skill as a callable sub-routine rather than re-deriving it — a
   real, checkable compositionality claim, explicitly flagged as unproven and gated at
   Stage 6, not assumed.
10. **Best end-to-end design**: the Verified Skill Ledger, as fully specified in §15–26.
11. **Cheapest way to prove it wrong before heavy investment**: §29's kill test — a
    single matched-compute comparison between best-effort prompting and a tiny
    search-and-verify loop, on one already-characterized real bug family, at a cost
    comparable to probes already run this session.

---

**Conditions under which I would abandon this recommendation**: if §29's kill test shows
best-effort prompting already matches search-and-verify's pass rate (the core variation
mechanism adds nothing); if Stage 2's held-out gate cannot be made to fire successfully
even once after real engineering effort (suggesting the generalization problem is harder
than this design assumes); or if RiverBrain's own existing statistics are found to be
near a discrimination ceiling as observation counts grow (weakening the case that the
SELECTION half of this architecture still has real headroom).
