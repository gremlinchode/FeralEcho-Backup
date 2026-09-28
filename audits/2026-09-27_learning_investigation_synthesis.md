# Learning Investigation Synthesis: Bottleneck Diagnosis and Solution Search

**Read-only synthesis. No model calls, no code changes, no production modifications, no
new experiments.** All standing results (persistent-routing null, strategy-characterization
Outcome E, G3 negative, belief-revision negative) are preserved exactly as reported —
nothing below reinterprets them. This memo re-derives its evidence ledger from primary
artifacts (re-read during this pass, not assumed from the mission's own summary), and
adds several previously-unexamined artifacts that materially sharpen the picture:
`attempt_ledger_test`, `provenance_f2_verification`, `retrieval_capacity_proof`,
`minimal_relevance_gate`, and `first_learning_loop`'s own trial data.

---

## 1. Executive conclusion

**FeralEcho has one clean, real, demonstrated example of acquired competence — and it
looks nothing like any of the mechanisms this research arc has spent the last several
missions testing.** RiverBrain's `model_task_stats` (a running per-model, per-task-type
quality estimate, updated from real verified outcomes, consumed by the self-edit fitness
gate to reject regressions) is a genuine instance of experience → retained numerical
state → causally consequential later decision, restart-surviving, already running in
production for months. It requires **zero natural-language hypothesis generation**. Every
mechanism this arc built that *does* require the model to verbalize a causal explanation
— VECT's true autonomous-extraction gap, G3's diagnostic-to-inference step, the
belief-revision probe — has failed, cleanly and repeatedly, at exactly that verbalization
step. The bottleneck is not persistence (we have working, rigorous persistence machinery
in at least three independent forms), and it is not evaluation (the oracle
infrastructure is arguably the strongest, most reused asset in the whole arc). **The
bottleneck is that we have been asking a 7B local coding model to perform reliable causal
inference in natural language as a prerequisite for learning, when the one substrate
that has actually worked in this exact codebase does not require that step at all.**

---

## 2. Evidence ledger (re-derived from primary artifacts)

| Investigation | Classification | Basis |
|---|---|---|
| RiverBrain `model_task_stats` (Findings 10, 39, 44, 91) | **DEMONSTRATED** | Real per-(model, task_type) running quality estimate, updated from real oracle/quality-scorer outcomes, consumed by `execute_self_edit()`'s fitness gate (Finding 19) to reject non-improving candidates — verified live in production repeatedly across this project's history, restart-surviving (a pickle file), causally consequential (rejections are logged with the exact comparison). |
| `attempt_ledger_test` (re-read this pass) | **APPARATUS / MEASUREMENT RESULT ONLY** | Confirms `river_brain.pkl`'s hash is byte-identical before/after a real *rejected* attempt — a correct negative control (rejection doesn't spuriously mutate state), not itself a positive learning demonstration. |
| `provenance_f2_verification` (re-read this pass) | **NOT ESTABLISHED** | **Confirms 0 real, joinable `trace_id`↔F2-verdict pairs exist in current production data** — the trace_id plumbing (Finding 92) is real but not yet flowing end-to-end for self-edit outcomes specifically; the file's own "ledger" is an explicitly-labeled isolated simulation of what such a join *would* do. |
| Council-rating→RiverBrain blend (Finding 67) | **DEMONSTRATED, narrow** | A real, trust-gated (`council_baseline_trusted_since`) additional training signal wired into the same non-verbal statistical substrate as above — same substrate, same reason it works. |
| VECT (`validated_experience_competence_transfer`) | **PARTIALLY DEMONSTRATED, materially qualified** | Real measured advantage (P=10/10 vs G=6/10 vs Z=5/10); **P is investigator-authored** (direct read of `freeze_procedure.py`: a literal string, verified only by episode-ID existence, never algorithmically derived); original "unseen instances" claim was too strong (TRAIN/held-out shared all 4 code bodies by pigeonhole — caught by the self-falsification review). |
| Restart-persistence-of-P (`restart_persistence_transfer`) | **DEMONSTRATED, narrow** | Real OS-process restart boundary (distinct PIDs, distinct `id(sys.modules)`), real fresh held-out content, 9/10 vs 4/10, mechanistically traced to P's own clauses. Persists the *externally-authored* artifact — does not close the acquisition-provenance gap, and its own report says so explicitly. |
| `persistent_routing` (this session) | **FALSIFIED UNDER TESTED CONDITIONS** | 3/3 lineages: real state change (S0≠S1, content-hashed) but zero effect on any of 12 real holdout evaluations. Root-caused, not just observed: one holdout bucket structurally unreachable, the other bucket's real update never displaced the default in 2/3 lineages and correctly didn't in the third. |
| `strategy_characterization` (this session) | **NOT ESTABLISHED (Outcome E, honestly inconclusive)** | Primary template-level Friedman n=6, p=0.0907 — not significant, but the design's own pre-registered power analysis predicted this exact outcome for a moderate real effect; not reinterpreted as positive or as proof of equivalence. |
| Forensic mining of the 216-generation dataset (this session) | **DEMONSTRATED (as a measurement), R4 exploratory classification** | Real, world-replicated, mechanistically-traced bug families (field-extraction shape errors; parameter-mishandling) exist in the data. `oracle_runner.grade()` already exposes rich per-failure diagnostic text; `extract_sanitized_outcome()` (persistent_routing) discards it by design. This is a real architectural fact, not a hypothesis. |
| G3 micro-probe (this session) | **FALSIFIED UNDER TESTED CONDITIONS** | 0/7 correct diagnoses; 0/7 corrections passed the real oracle (mechanically verified, not assumed); 5/7 converged on the identical incorrect "negation" theory regardless of whether real diagnostic evidence was shown; confidence 0.95–1.0 throughout. |
| Belief-revision probe (this session) | **FALSIFIED UNDER TESTED CONDITIONS** | 3/3 episodes: confidence dropped 1.0→0.8 uniformly (a suspiciously mechanical decrement); 2/3 redirected doubt toward the evaluator rather than revising the code-mechanism belief; 0/3 produced a materially different, testable hypothesis. |
| `first_learning_loop` (re-read this pass, corroborating VECT's own self-falsification §7.1) | **NOT ESTABLISHED** | Real, mechanically-verified (not LLM-self-reported) mining of historical NameError→retry-success patterns from watchdog logs — a genuinely automated extraction step, further than any other experiment in the arc got toward automating G3. But its "lesson" is a **fixed, investigator-authored sentence template** filled with mined facts, and its own recorded transfer trial shows a case with byte-identical control/experience generated code — no measurable advantage demonstrated in the one pair inspected. |
| `architecture_a_hot_stove_proof` | **FALSIFIED UNDER TESTED CONDITIONS** | 6 control vs 6 experience trials, 5/6 retry-success in *both* conditions — a real null on the production self-edit sandbox/importability path with a failure-derived diagnostic injected. |
| `retrieval_capacity_proof` / `minimal_relevance_gate` (re-read this pass) | **APPARATUS / MEASUREMENT RESULT ONLY** | Test whether *richer representations* of the same fact (raw error → diagnosis → diagnosis+correction → full synthetic causal record) would be retrieved/judged relevant differently. The richest representation (X4) is explicitly labeled `[SYNTHETIC EXPERIMENTAL RECORD, not a real Echo memory]` — this tests a hypothetical richer memory format's retrieval behavior, not a demonstrated acquisition. Real, useful finding buried in it: even X4's rich causal structure is correctly judged `NOT_RELEVANT`/`NO_USEFUL_MEMORY` against a topically distant query by the real relevance-gate features (topic/identifier overlap) — a sobering, concrete data point about how narrow naive relevance-gating is. |
| `learning/` micro-world retention pilot (cited via VECT's self-falsification §7.4) | **PARTIALLY DEMONSTRATED** | Persistent-memory retrieval condition genuinely contains the formation information (stronger than an empty-memory claim) but produces incorrect answers on a novel category — real retrieval, unreliable use. |
| Council-rater trust threshold (Finding 67's own precondition) | **DEMONSTRATED** | `council_baseline_trusted_since` genuinely, automatically set once real thresholds were crossed (2026-07-22) — a real instance of an *automatic* trust/gating trigger firing correctly, worth noting as a working precedent for automatic (non-manual) gate-crossing. |

---

## 3. Innate / contextual / retrieved / acquired — separated per claim

- **Innate (A)**: qwen2.5-coder:7b's baseline ability to write a plausible-looking
  multi-key sort (correct in shape, wrong in the specific tag-priority direction/
  field-projection details) — this is what both the G3 CONTROL arms and the original
  Stage-1 failures already show, unaided.
- **Contextual (B)**: VECT's P, restart-persistence's recovered P, `first_learning_loop`'s
  templated sentence — all are *contextual* once loaded into a fresh prompt; the
  question the arc kept trying to answer was whether the *content itself* was acquired,
  not whether context helps (it demonstrably does, per VECT's own real P-vs-Z gap).
- **Retrieved (C)**: the `learning/` micro-world pilot's persistent-retrieval condition —
  genuine retrieval of previously-stored information, imperfectly used.
- **Acquired (D) — the hard category.** **The strongest clean example is RiverBrain's
  `model_task_stats`.** It is retained (a pickle, restart-surviving), it changes with
  real experience (verified outcomes update the running mean), and it causally affects
  a later decision (the fitness gate). It required no natural-language hypothesis at any
  point. **No clean example of autonomously-verbalized acquired competence exists in this
  codebase** — VECT's real P was investigator-authored; `first_learning_loop`'s lesson is
  template-filled, not derived; G3 and belief-revision, this session's own direct tests
  of the verbalization step, both failed. This should be said plainly, not softened:
  **the project has never once demonstrated a model deriving, in natural language, a
  correct generalizable lesson from its own diagnostic evidence.**

---

## 4. Learning-chain bottleneck map

| Link | Machinery exists? | Demonstrated? | Failed experimentally? | Never tested? |
|---|---|---|---|---|
| experience | Yes, extensively (every experiment package) | Yes | — | — |
| observation (independent oracle) | Yes, `oracle_runner.grade()`/`sandbox.run_candidate()`, reused across 6+ experiments | Yes, repeatedly, real sandboxed execution | — | — |
| candidate change (a proposed correction/lesson) | Partial — `format_failure_feedback()`/`output_tail` exist; no code path derives a *candidate* from them autonomously except this session's G3 probe | RiverBrain's *numerical* candidate update: yes. Verbal candidate generation: **failed** (G3: 0/7) | G3, belief-revision | — |
| evaluation of the candidate | Yes, same oracle infrastructure | Yes, for numerical updates (fitness gate); for verbal candidates, this session mechanically verified 0/7 pass | Same as above | — |
| retention (validated-only) | Real templates exist (`persistent_routing/selector.py`, `freeze_procedure.py`-style hash-then-freeze) | Yes for numerical state (RiverBrain); for verbal candidates, never reached — nothing to retain | — | Retention-of-a-genuinely-derived-verbal-candidate: never reached |
| restart survival | **Demonstrated twice, rigorously** (`restart_persistence_transfer`'s distinct-PID design; RiverBrain's own pickle) | Yes | — | — |
| later autonomous use | Mechanically demonstrated (`persistent_routing`'s S1 loads and is consulted) | Behaviorally: **failed** (persistent_routing 3/3 null — retrieval happened, never changed a decision) | persistent_routing | — |
| measurable consequence | — | RiverBrain: yes (fitness-gate rejections). Verbal-lesson-based: never reached a live consequence test | persistent_routing (measured, found none) | — |
| counterfactual removal/substitution | **The single most rigorously-built piece of machinery in the whole arc** — `replay.py`'s TRUE/SHAM design, independently verified 10/10 before trust | Yes, mechanically proven correct | — | Never applied to a genuinely-derived verbal candidate (nothing has reached that stage) |
| accumulation | — | No | — | Never attempted — correctly, per every mission's own explicit scoping |

**The bottleneck map's own shape is the finding**: everything *around* candidate
generation — observation, evaluation, retention mechanics, restart survival, causal
substitution — is either fully demonstrated or has genuinely excellent, reusable
infrastructure. **The one link that has never once succeeded is candidate generation
itself, specifically in its verbalized form.**

---

## 5–6. What the recent negative probes establish, and do not

**Establish**: that this specific 7B local model, asked directly and without scaffolding
to infer a causal mechanism from one real diagnostic example and state it in natural
language, does not reliably do so (G3), and does not reliably revise that stated belief
in a materially different, evidence-tracking way when it is falsified (belief-revision).
Both are real, mechanically-verified (not assumed) negative results, each on a small but
carefully-designed and adversarially-reviewed probe.

**Do not establish**: that FeralEcho cannot learn; that persistence/memory machinery is
worthless (RiverBrain's own working example uses exactly that machinery); that larger or
different models would fail the same way; that a *non-verbal* candidate-generation
mechanism (search, selection, statistical update) would fail the same way — this was
never tested, because every probe so far specifically tested the verbal-hypothesis
substrate. **Conflating "verbal causal inference is unreliable in this model" with "this
model/architecture cannot learn" would be a real, avoidable overreach.**

---

## 7. Ranked bottleneck diagnosis

1. **Architecture mismatch — demanding verbalized causal inference as the learning
   substrate.** *For*: G3 (0/7), belief-revision (0/3 materially different), while
   RiverBrain's non-verbal numerical substrate works reliably in the same codebase.
   *Against*: `first_learning_loop`'s mechanically-verified (non-LLM) extraction shows
   *some* automated, non-verbal signal extraction is real and works — the mismatch is
   specifically the *verbal generalization* step, not automation itself. *Confidence*:
   high. *Would change my mind*: a clean demonstration of a 7B local model correctly
   verbalizing a causal mechanism from diagnostic evidence on a genuinely comparable
   task, even once, under the same controls G3 used.
2. **Model capability ceiling for this specific inference class.** *For*: 0/7 with
   uniform high confidence suggests not "occasionally right, occasionally wrong" but
   "confidently pattern-matches to a generic, wrong, frequently-seen bug template" —
   consistent with a real capability gap for this reasoning class at this model size.
   *Against*: the *code-generation* capability (producing structurally correct, if
   subtly-wrong, sorts) is clearly present — this isn't a blanket capability floor, it's
   specific to root-cause diagnosis from a single example. *Confidence*: moderate-high.
   *Would change my mind*: the same probe run against a larger or differently-trained
   model showing materially better mechanism identification.
3. **Training-signal quality / credit assignment for verbal candidates.** *For*:
   nothing in this codebase currently scores or filters a verbal candidate's *causal
   correctness* before it would be retained — G3 had no such filter, by design (feasibility
   probe only). *Against*: this presupposes candidate generation already works well
   enough to need filtering, which it doesn't yet. *Confidence*: low as an independent
   bottleneck (downstream of #1/#2). *Would change my mind*: a version of G3 with many
   more candidates per episode, filtered by a real correctness check, showing the *best*
   of several candidates is reliably good even when the *typical* one isn't (a
   search-shaped signal, distinct from the single-shot inference this session tested).
4. **Not** persistence, not retention mechanics, not restart survival, not causal
   substitution — all four have real, working, independently-verified implementations
   already. Ranking these as low-priority bottlenecks is itself evidence-grounded, not
   assumed: `replay.py`'s 10/10 verification and `restart_persistence_transfer`'s
   distinct-PID design are both real, already-proven capabilities sitting mostly unused
   because nothing upstream has produced a genuine artifact worth persisting through them
   yet.

---

## 8. Comparison with established learning paradigms

Paradigms that **address the actual diagnosed bottleneck** (candidate generation, not
persistence): **verifier-guided generation / search-and-select**, **self-training with a
real filter**, **process supervision** (reward the *reasoning trace* against ground
truth, not just the final answer), **parameter-efficient fine-tuning on a smaller,
trainable model**. Paradigms that would **mostly re-test something already falsified**:
another Reflexion-style "reflect in natural language and retry" loop — this is
structurally identical to what the belief-revision probe already tested and found
weak (verbal self-correction without a materially different causal claim). A
memory-augmentation / RAG-heavier design would mostly extend a link (retrieval) that
already works and isn't the bottleneck.

---

## 9. Real-world feasibility under FeralEcho's actual constraints

- **Immediately feasible**: a verifier-guided search loop (generate N candidates,
  filter by the existing oracle, retain the survivor) — reuses `oracle_runner.grade()`,
  `replay.py`'s substitution pattern, and `RiverBrain`'s existing update contract
  directly; no new training infrastructure needed.
- **Feasible with moderate engineering**: LoRA/adapter fine-tuning of a smaller local
  model (e.g. a 1–3B model) on accumulated real (attempt, verified-outcome) pairs — this
  machine already runs local inference; LoRA training of a small model is realistic on
  Apple-silicon-class hardware, though real (untested here) engineering effort.
- **Research-heavy**: a genuine skill-library / program-synthesis-search architecture
  with mutation and reuse.
- **Currently impractical**: fine-tuning or adapting the actual conversational/synthesis
  model (`echo:latest`, `qwen2.5-coder:7b` at full size) — no training infrastructure for
  models this size exists in this codebase, and building one is a materially larger
  undertaking than anything attempted in this whole research arc to date.

---

## 10–12. Three genuinely different solution paths

### Path A — Verifier-guided search over executable procedures (not beliefs)

**Mechanism**: generate multiple candidate corrections per real failure (no
single-shot causal inference required); run each through the existing oracle; retain
only the survivor, as *code*, not as a verbalized lesson. **Learning signal**: real
pass/fail, exactly as already proven throughout this arc. **Substrate**: a small,
versioned library of executable, oracle-verified corrections, keyed by a *mechanical*
feature of the failure (not a verbal diagnosis) — e.g., task template + failure-class
tuple, reusing `dimensions.py`'s own pre-declared, non-post-hoc dimension discipline.
**Consumer**: a lookup at generation time, structurally identical to `persistent_routing`'s
own selector (a proven, already-built mechanism) but keyed by *task shape*, not
*strategy choice*. **Persistence**: the same hash-then-freeze pattern already proven three
times in this codebase. **Generalization**: a retained correction generalizes exactly as
far as its keying feature does — testable directly, not assumed. **Causal test**: reuse
`replay.py`'s TRUE/SHAM substitution design directly — already built, already verified.
**Accumulation**: each new verified correction adds one library entry; N+1 doesn't
require N to have been verbalized correctly, only verified. **Failure modes**: could
degenerate into instance-specific memorization if the keying feature is too narrow —
mitigated by requiring the held-out generalization test before retention, exactly as
`strategy_characterization`'s Stage 2 gate already specified. **Cost**: moderate — more
generations per failure (a small multiplier, not a new infrastructure category).
**Compatibility**: very high — reuses `oracle_runner`, `replay.py`, `persistent_routing`'s
selector shape, and `dimensions.py`'s discipline almost unmodified.

### Path B — Extend RiverBrain's already-working substrate, deliberately, instead of building a new one

**Mechanism**: rather than inventing a new learning mechanism, extend the *one* substrate
already proven to work — add new, narrowly-scoped numerical/statistical signals (e.g.,
per-failure-class success rates, not just per-model/per-task-type) to RiverBrain's
existing `model_task_stats` shape, consumed by existing gates (the fitness gate, the
model-selection entropy signal). **Learning signal**: real verified outcomes, exactly
RiverBrain's existing contract. **Substrate**: RiverBrain itself — no new file format,
no new persistence mechanism. **Consumer**: existing consumers (`execute_self_edit()`'s
fitness gate, `choose_model()`). **Persistence**: already solved (the existing pickle).
**Generalization**: bounded by whatever key is added (e.g., failure-class) — same
caveat as Path A. **Causal test**: directly comparable to `attempt_ledger_test`'s
already-proven hash-diff technique. **Accumulation**: RiverBrain already accumulates
(observation counts climb over months of real production use) — this path's main
contribution is finer-grained keys, not a new accumulation mechanism. **Failure modes**:
risk of diluting RiverBrain's existing, working signal with a noisier new one — mitigate
by keeping any new key strictly additive, never replacing existing fields (the same
discipline Finding 35's `self_edit_coding` bucket addition already used). **Cost**: low
— this is the cheapest path by a wide margin. **Compatibility**: maximal — this *is* the
existing architecture, extended, not replaced.

### Path C — Separate a small, trainable local model as the "learner," keep the large model as the "actor"

**Mechanism**: introduce a genuinely trainable small model (1–3B class) whose only job is
candidate-correction generation, periodically fine-tuned (LoRA) on accumulated real
(failure, verified-correction) pairs mined by something like `first_learning_loop`'s
already-proven mechanical extraction — but feeding a *trainable* consumer instead of a
fixed authored template. **Learning signal**: real verified outcomes, used as supervised
fine-tuning targets, not verbalized lessons. **Substrate**: the small model's own weights
(a genuine parameter-level update, addressing Section 15's hypothesis directly).
**Consumer**: the small model itself, invoked as a component (a "corrector" role)
alongside the existing large-model actor. **Persistence**: a versioned adapter/weight
file — genuinely restart-surviving by construction. **Generalization**: an empirical
question, testable directly (held-out fine-tuning evaluation, a standard, well-understood
methodology, distinct from anything tried in this arc). **Causal test**: compare the
fine-tuned adapter against a frozen/rolled-back version on identical held-out cases —
directly analogous to `replay.py`'s own substitution logic, applied to weights instead of
a JSON file. **Accumulation**: each fine-tuning round is a new checkpoint; whether
competence compounds across rounds is the central open question this path would need to
answer, honestly, before claiming success. **Failure modes**: catastrophic forgetting
(a real, well-documented risk for small-model fine-tuning); evaluation contamination if
training and held-out data aren't kept genuinely disjoint (this arc's own repeated,
hard-won discipline — VECT's pigeonhole mistake — applies directly here too). **Cost**:
the highest of the three — real training infrastructure, real GPU/Apple-silicon time,
real engineering to keep provenance and rollback rigorous. **Compatibility**: moderate —
reuses the oracle and provenance conventions, but requires genuinely new
training/adapter-management code this arc has never built.

---

## 13. First-principles redesign

**If I were designing this today, keeping only the project goal, available hardware, the
hard-won experimental lessons, and the provenance/evaluation infrastructure**: I would
build Path A first, not Path C. The reasoning: this whole research arc's own accumulated
lessons (VECT's authorship gap, G3's inference failure, belief-revision's evasiveness)
all point at the same root cause — **we kept asking a fixed, frozen, 7B model to do
something it isn't reliably good at (verbalized causal inference) as a gate before
learning could occur at all.** Search-and-verify sidesteps that gate entirely: it never
requires the model to *say* why something failed, only to *produce alternatives* and let
the already-excellent, already-proven oracle decide. This is the version of "start over"
that actually uses everything real that's been built (the oracle, `replay.py`,
`persistent_routing`'s selector shape, `dimensions.py`'s pre-registration discipline) and
discards only the one component that has never once worked (single-shot verbal
diagnosis as a prerequisite).

---

## 14. Minimal accumulated-competence demonstrator

**Smallest credible system**: take exactly one real, already-catalogued K2 bug family
(e.g., EP-A's tag-priority-direction inversion). At T1, generate 5 candidate corrections
(no verbalization required, just code) for one real failing instance; verify each against
the oracle; retain the one real survivor, keyed only by "this exact bug's mechanical
signature" (not a verbal lesson). At T2, present a genuinely novel instance of the *same*
mechanical signature (a fresh world, same real bug shape) and check whether looking up
and applying the retained survivor measurably improves pass rate over a frozen control
with no retained artifact — reusing `replay.py`'s exact substitution design to prove the
retained artifact, not chance, causes the difference. If T2 succeeds, ask whether solving
T2 required capability *not present* at T1 (a genuine test of whether T1's competence
gain enables something new) — this is the T3 accumulation check the mission's own Section
14 asks for, and it's answerable with the infrastructure already built, at a cost far
below any of the three paths above (single-digit-to-low-double-digit real calls, matching
this session's own G3/belief-revision budget discipline).

---

## 15. Trainable-local-model assessment (Section 15, direct answer)

**Feasible in principle, not assessed as the first move.** A small (1–3B) open-weight
model could plausibly undergo LoRA fine-tuning on Apple-silicon-class hardware within
FeralEcho's real constraints. Catastrophic forgetting, evaluation contamination, and
rollback are all real, non-trivial risks this codebase has never had to manage (its
entire model-adaptation history to date is *external memory*, never weight updates) —
this would be genuinely new engineering territory, not an extension of anything proven.
**Compared honestly against Path A**: Path A can be built entirely from already-proven
components and directly tests the actual diagnosed bottleneck (candidate generation)
without introducing a new, unproven risk category (weight-update rollback/forgetting).
Path C remains a legitimate, real second step if Path A itself hits a ceiling — but
building it first would mean solving a harder infrastructure problem before confirming
the easier one (search-and-verify) doesn't already suffice.

## 16. Search + verification assessment (Section 16, direct answer)

**This is Path A**, restated: generate alternatives, verify mechanically, retain the
survivor as an executable artifact. **Distinguishing this from random retrying**: the
retained artifact must be keyed by a *pre-declared, mechanical* feature of the failure
(not chosen after seeing which correction happened to work — the same
post-hoc-feature-invention discipline `strategy_characterization`'s own corrected
protocol already established) and must pass a genuine held-out generalization test before
being trusted for reuse, mirroring VECT's own (contaminated, but structurally correct in
intent) TRAIN/HELD-OUT split, fixed the way `restart_persistence_transfer` fixed it (fresh
content, verified disjoint).

## 17. Hybrid options

The most promising near-term hybrid is **Path A feeding Path B**: search-and-verify
produces real, verified (failure-class, working-correction) pairs; rather than storing
these as a brand-new artifact type, fold the *outcome* (did a retained correction
generalize) into RiverBrain's existing accumulation as one more per-key statistic — this
gets Path B's near-zero marginal cost and Path A's actual bottleneck-addressing mechanism
in one move, with no new persistence format.

---

## 18. Adversarial attack on the #1 recommendation (Path A)

**Attempted kills:**
- *"It's just another non-learning doppelgänger — a lookup table of pre-verified fixes,
  not learning."* Real risk, honestly conceded: if the keying feature is narrow enough,
  this degenerates into exactly VECT's own already-diagnosed problem (a finite answer
  bank). **Mitigation, not full defense**: the held-out generalization gate is what
  separates a lookup table from a genuinely reusable fix — but this gate has never
  actually been exercised successfully in this arc (Stage 2 never triggered in
  `strategy_characterization`; VECT's own held-out set was contaminated before its
  fix). This is a real, unresolved risk, not a solved one.
- *"It will overfit to the specific failure shapes already catalogued from Stage 1."*
  Plausible — the three bug families used to motivate this design (EP-A/B/C) are the
  only ones deeply characterized so far. Mitigation: the design must be tested against
  bug families *not* used to design it, which this memo has not yet done.
- *"The base model already explains any observed improvement — search-and-verify just
  finds the correction the model could have written on the first try with better
  prompting."* A real, serious doppelganger. **This is checkable directly**: if a single,
  better-engineered CONTROL prompt (not a search loop) reaches the same pass rate as the
  retained-survivor condition, Path A adds nothing beyond prompt engineering. This has
  **not** been tested and is the single most important gap in this recommendation.
- *"Evaluation leakage."* Lower risk than in prior experiments specifically because the
  oracle infrastructure being reused has already been independently hardened across six+
  prior experiments in this exact codebase — but not zero risk, and must be re-verified
  for this specific use, not assumed transferred.

**Verdict: the recommendation survives, but conditionally, not cleanly.** It survives
because it is the only path that (a) reuses proven infrastructure, (b) directly targets
the diagnosed bottleneck, and (c) is cheap enough to test the "base model already
explains it" doppelganger directly before any larger investment — which is exactly what
Section 22's smallest-next-investigation should be, not a reason to abandon the path.

---

## 19. STOP list

- **Verbal-hypothesis-based candidate generation as a learning prerequisite** (the exact
  substrate G3 and belief-revision tested) — stop, on this model, until a materially
  different model or scaffold shows even one clean success on a comparable probe.
- **Further K2-family debugging experiments of any kind** — per this mission's own
  explicit instruction, and because the diagnostic value of this specific task family has
  been thoroughly extracted (three independent probes, three independent negative
  results, all mechanistically explained).
- **Further single-shot verbal belief-revision probes** — the specific failure mode
  (evidence-invalidation rather than revision) is now well-characterized; repeating the
  same probe shape on new episodes would not add new information without first changing
  the substrate being tested.
- **Any further persistence/restart/substitution *infrastructure* building** — three
  independent, rigorous implementations already exist (`replay.py`,
  `restart_persistence_transfer`, `persistent_routing`'s own S0/S1 mechanism). Building a
  fourth without a genuine artifact to persist would be solving an already-solved problem.

**Reopen conditions, stated for each**: verbal-hypothesis generation — reopen if a
different model or a scaffolded (chain-of-thought, multi-sample) version of the same
probe shows a real, mechanically-verified success rate meaningfully above the observed
0/7. K2 debugging — reopen only if a genuinely new task family reveals a qualitatively
different failure pattern worth characterizing. Belief-revision — reopen only paired with
a changed substrate (e.g., testing revision over *executable candidates* rather than
verbal claims). Persistence infrastructure — reopen only when Path A or B produces a
real, validated artifact that the existing three mechanisms don't already know how to
persist.

## 20. KEEP list

- **The independent oracle infrastructure** (`oracle_runner.grade()`,
  `sandbox.run_candidate()`) — the single most reused, most battle-tested asset in the
  entire arc; every genuine finding in this whole research program traces back to it.
- **`replay.py`'s TRUE/SHAM substitution design** — the most rigorous causal-attribution
  mechanism built in this codebase, independently verified before trust, directly reusable
  by any of the three proposed paths.
- **The restart/process-boundary evidence standard** (`restart_persistence_transfer`'s
  distinct-PID, distinct-`id(sys.modules)` discipline) — a real, proven bar for a claim
  that's easy to fake and hard to prove.
- **RiverBrain's `model_task_stats` substrate itself** — the one demonstrated working
  example of acquired competence in the whole project; extending it (Path B) costs far
  less than replacing it.
- **The pre-registration/adversarial-review/provenance-hash discipline** established
  across every experiment this session touched — this is *why* the negative results in
  this ledger are trustworthy rather than merely asserted.
- **The mechanical, non-LLM-self-report extraction pattern** (`first_learning_loop`'s
  verified-retry-matching) — even though its current output (a fixed template) is
  limited, the *extraction* half of that pipeline is real and reusable as an input to
  Path A/C's own candidate-mining step.

---

## 21. Recommended research direction

**Path A (verifier-guided search over executable procedures), with Path B as a
near-zero-cost parallel extension.** Not Path C, not yet — Path C solves a harder
problem (weight-level adaptation with its own new risk category) before confirming the
cheaper, evidence-aligned alternative doesn't already suffice.

## 22. Smallest next investigation

**Directly attack Section 18's most serious unresolved doppelganger, before building
anything else**: take one real K2 bug family (EP-A), and compare (a) a single,
carefully-engineered CONTROL prompt (best-effort prompt engineering, zero search) against
(b) a small search-and-verify loop (5 candidates, oracle-filtered) on the *same* real
failing instances. If (a) already matches (b)'s pass rate, Path A's core mechanism adds
nothing beyond prompt quality, and the recommendation must be revised before any further
investment. This is answerable within a call budget comparable to this session's own
G3/belief-revision probes (single-digit to low-double-digit real calls), not a large
undertaking.

## 23. Conditions that would change this recommendation

- A clean, mechanically-verified success (even one) of verbal causal inference on a
  comparable probe would reopen the verbal-hypothesis substrate and weaken the case for
  routing around it entirely.
- A negative result on Section 22's own smallest-next-investigation (CONTROL matches
  search-and-verify) would kill Path A's core premise and shift the recommendation toward
  Path C or a genuinely different mechanism not yet considered.
- Evidence that RiverBrain's existing substrate is already near a ceiling (e.g., its
  accumulated statistics no longer discriminate meaningfully as observation counts grow)
  would weaken Path B's near-zero-cost argument.

---

## Final questions, answered directly

1. **Strongest demonstrated learning capability**: RiverBrain's `model_task_stats` —
   real, restart-surviving, causally consequential, accumulated over real production
   experience, requiring no verbal hypothesis.
2. **Strongest capability *not* demonstrated**: a model autonomously deriving, in natural
   language, a correct, generalizable causal explanation from its own diagnostic
   evidence — tested directly and specifically (G3, belief-revision) and failed both
   times, mechanically verified, not assumed.
3. **Where the bottleneck most likely sits**: candidate generation, specifically the
   verbalization step — not persistence, not evaluation, not retention mechanics, all of
   which are demonstrated and working.
4. **Wrong architectural layer?** Yes — the arc has been building increasingly rigorous
   persistence/restart/substitution machinery (the *downstream* layers) around a
   candidate-generation step (the *upstream* layer) that has never once produced a valid
   artifact to persist.
5. **If I controlled the project from here**: build Section 22's smallest investigation
   first (search-and-verify vs. best-effort prompting, same real bug family), then Path A
   proper if it survives, with Path B wired in parallel at near-zero marginal cost.
6. **What I would stop doing**: everything on the Section 19 STOP list — most centrally,
   asking this model to verbalize causal explanations as a prerequisite for any further
   learning experiment.
7. **What I would preserve**: the oracle infrastructure, `replay.py`'s substitution
   design, the restart-evidence standard, RiverBrain's own substrate, and the
   pre-registration/provenance discipline that made every negative result in this ledger
   trustworthy.
8. **What Gremlin and ChatGPT may have overlooked**: that the project's own best working
   example of "acquired competence" (RiverBrain) was sitting the entire time as a
   counter-example to the assumption — implicit across VECT, G3, and belief-revision —
   that a verbalized lesson is the natural or necessary substrate for learning here.
9. **Highest-confidence path toward experience→retained change→improved
   competence→reuse→further acquisition, not merely experience→storage→retrieval**:
   Path A, specifically because its "retained change" is a verified executable artifact,
   not a claim about one, and its "reuse" step is a mechanical lookup, not a hope that a
   verbal lesson will be correctly re-applied.
10. **Smallest experiment that could falsify this before heavy investment**: Section 22's
    own proposal — a single comparison between best-effort prompting and a tiny
    search-and-verify loop on one already-characterized real bug family, at a cost
    comparable to the G3/belief-revision probes already run this session.
