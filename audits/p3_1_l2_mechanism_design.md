# P3.1 — Smallest Architectural Intervention for an L2-Capable State Channel

**Mode: pure design comparison. No code was written or modified for this document. No live model
call was made. Nothing in P1, P1.2, P2, the Learning Investigation, or P3 was touched.**

## Question

What is the smallest architectural intervention that could give Echo a persistent behavioral state
channel capable of L2 (per the P3 hierarchy: a restart-durable state that changes generated *content*,
not merely *routing*, and does not work by re-presenting the original teaching text) without becoming
mere FAISS retrieval or RiverBrain-style routing?

## The sharp conceptual problem this question raises, addressed directly rather than glossed over

Echo's underlying model weights are never fine-tuned anywhere in this architecture (confirmed across
every prior audit in this thread). This means **any** mechanism that changes what a frozen-weight
model says must, at some point, place *some* text into its context for it to read and act on. Taken
naively, this makes "genuine L2" and "L1-flavored retrieval" look indistinguishable — both ultimately
reduce to "text was in context, the model followed it." The distinction this design insists on
preserving is not "no text in context ever," but three narrower, checkable properties:

1. **What gets stored is a *derived, abstracted* representation of an experience, not the original
   teaching exchange itself.** FAISS stores and (probabilistically) resurfaces the verbatim
   conversation. A genuine L2 channel's mutation step must *discard* the original text and persist
   only a distilled directive/rule/scalar — the literal teaching sentence is never what's read back.
2. **What decides to surface it is a deterministic, bounded read of an explicit, small state store —
   not a similarity search over an ever-growing, unstructured pile of raw history.** This is checkable
   and auditable in a way "did the embedding happen to be close enough" is not (the Learning
   Investigation's own pilot data already showed real, sometimes-surprising retrieval misses for
   exactly this reason).
3. **The mutation step itself has explicit, inspectable provenance** (what experience triggered it, when,
   under what review) — distinct from FAISS's implicit, automatic, unreviewed logging of every
   conversational turn.

Every design below is judged against these three properties, not against the shallower and
unanswerable "is there text in context" question.

## A structural head start already exists and should not be re-invented

`echo_ground_truth.py`'s keyword-gated slice mechanism (`_build_capabilities()`, `_build_affect()`,
etc.) is **already a confirmed-working, twice-independently-audited READ→GENERATION path** — it reads
a small, structured state file (`self_model.json`) and renders it as system-prompt content on every
real conversational entry point. This means the harder, already-solved half of the required chain
(`STATE_READ → BEHAVIOR`) does not need to be invented for Options 1 or 2 below — only a new,
dedicated state file and a new slice function following the identical, already-proven pattern. This
materially lowers the cost and risk of the two smallest candidates, and is cited explicitly wherever
it applies below.

---

## Candidate 1 — Minimal scalar/structured behavioral state

A small, bounded, human-readable JSON file (its own new path, e.g.
`memory/behavioral_directives.json` — never overlapping with any existing production memory file,
any sibling experiment's own state root, or P1/P1.2/Learning-Pilot evidence) holding a short list of
named directives, each with an explicit trigger condition and a distilled instruction — e.g.
`{"trigger_keywords": ["code review"], "directive": "prefer terse, line-by-line feedback over prose summaries"}`.

**Chain:**
```
EXPERIENCE (an explicit teaching event, human- or model-proposed, NOT automatic logging)
  → STATE_MUTATION (a dedicated, narrow function -- NOT RiverBrain.learn(), NOT add_to_vector_memory()
    -- appends/updates one named directive, discarding the original conversation text)
  → PERSIST (atomic JSON write, same convention as every other small state file in this codebase)
  → RELOAD (read fresh at process start, or on each read call -- no complex reload logic needed
    given the file's small size)
  → STATE_READ (a new, small function, following echo_ground_truth.py's own established pattern:
    deterministic keyword/trigger match against the current prompt, never an embedding search)
  → BEHAVIOR (matched directive rendered into the system prompt, same injection point/mechanism
    already proven for self_model.json's slices)
```

- **COST:** Low. New state file, one narrow mutation function, one new slice function reusing an
  already-proven read/render/inject pattern. No new ML infrastructure, no new training loop.
- **RISK:** Low-moderate. The main risk is scope creep (the file becoming an unbounded dumping ground)
  and the new injection point needing its own leak/safety review (the same class of review
  `echo_ground_truth.py`'s existing slices already passed). Both are boundable by design (a hard cap
  on directive count, mirroring this project's own established `_MAX_SELF_EDIT_PLANS`/log-retention
  cap pattern).
- **CAUSAL_CLEANLINESS:** High. A directive either matches the deterministic trigger or it doesn't;
  the mutation step is explicit and narrow, not an automatic byproduct of ordinary conversation.
- **OBSERVABILITY:** High. A small, flat JSON file is trivially diffable, hashable, and human-readable
  — stronger observability than either FAISS (opaque vectors) or RiverBrain (pickled model state).
- **PERSISTENCE:** High. Same proven atomic-write convention as every other small state file in this
  codebase (`self_model.json`, `shadow_self_model.json`, etc.).
- **GENERALIZATION_POTENTIAL:** Low-moderate. A flat set of scalar/keyword-triggered dials generalizes
  only as far as the dial space is designed to cover; it does not naturally support compositional or
  conditional rules without starting to resemble Candidate 2.
- **CONFOUNDS:** The FAISS re-presentation confound is structurally impossible (nothing resembling the
  original conversation is ever stored). The remaining, honest confound: even a distilled directive is
  still *text read in context* — a skeptical read could call this "L1 with extra steps." This
  document's position, stated plainly: the distinction is real (derived vs. verbatim content;
  deterministic vs. similarity-driven read) but should be reported as such, not oversold as
  categorically different in some deeper sense.
- **REGRESSION_RISK:** Low. A small, capped state space with deterministic matching is unlikely to
  silently degrade unrelated conversations, unlike a similarity-search-driven or trained-model-driven
  mechanism.

## Candidate 2 — Learned policy/rule store

A richer version of Candidate 1: a JSONL, append-only rule store (mirroring the proven append-only
convention of `memory/dissent_log.jsonl`), each entry `{trigger_pattern, directive, provenance,
confidence, created_at}`, added to via an explicit `learn_rule()` call, read via deterministic
pattern-matching (regex/keyword, explicitly **not** embedding similarity) against the current prompt,
with conflict resolution when multiple rules match (e.g. most-specific-pattern-wins, or
most-recently-confirmed-wins — a real design decision to make later, not resolved here).

**Chain:** identical shape to Candidate 1, with a richer state schema and a real trigger-matching
layer instead of Candidate 1's flat keyword list.

- **COST:** Moderate. Needs a real pattern-matching read layer and a conflict-resolution policy for
  overlapping rules — meaningfully more code than Candidate 1, though still no ML training loop.
- **RISK:** Moderate-high. An accumulating, unpruned rule store risks the same staleness/bloat pattern
  this project's own history has repeatedly found in other accumulating logs (the reflection journal,
  the quarantine journal) — needs an explicit retention/pruning policy designed in from day one, not
  retrofitted later. Overly broad trigger patterns risk unintended firing in unrelated conversations —
  a real, practical failure mode distinct from anything FAISS or RiverBrain can produce (since neither
  injects a hand-authored behavioral directive into unrelated contexts the way a bad trigger pattern
  could).
- **CAUSAL_CLEANLINESS:** High, provided trigger-matching stays deterministic (exact/regex, not
  embedding similarity) — if similarity matching is ever added for "softer" trigger generalization,
  this collapses back toward FAISS's own re-presentation confound and should be treated as a distinct,
  higher-risk variant, not silently folded into this design.
- **OBSERVABILITY:** High. Append-only JSONL, same proven convention as the Dissent Log.
- **PERSISTENCE:** High.
- **GENERALIZATION_POTENTIAL:** Moderate-high. A genuine rule-based system can apply a taught policy
  to any novel prompt matching its trigger pattern — this is a real, meaningful step beyond
  Candidate 1's flat dial space, and is the natural target for testing L3 (generalization) once L2
  itself is established, per the P3 spec's own hierarchy.
- **CONFOUNDS:** Same "text read in context" honest caveat as Candidate 1. Additional confound: a
  false-positive trigger match (a marker word appearing coincidentally in an unrelated, real
  conversation) could produce behavior that looks like "generalization" but is actually a trigger-
  specificity bug — this must be distinguished carefully in any later measurement design, exactly as
  the P3 apparatus's own `verify_no_rule_leakage()` already does for its experimental probes.
- **REGRESSION_RISK:** Moderate. Requires active curation (pruning stale/low-confidence rules, a cap
  on total rule count) to avoid the same drift risk already documented elsewhere in this codebase.

## Candidate 3 — Stateful, trained preference/policy layer

A genuinely trained, incrementally-updated model (in the spirit of `river`'s own online-learning
approach, already used by RiverBrain) that maps a feature representation of the current prompt to a
content-steering directive, trained from explicit teaching signals, persisted as model weights,
reloaded at startup, read via real-time inference (not pattern-match, not similarity search).

- **COST:** High. Requires genuinely new ML infrastructure — feature engineering, a training loop,
  weight persistence/reload, and a new inference call on every relevant generation — substantially
  more engineering than either Candidate 1 or 2.
- **RISK:** High. **Directly conflicts with several of this mission's own MUST requirements.** A
  trained model's predictions are not deterministic in the same crisp sense as a rule match or a
  scalar read — "why did it predict this directive" is a harder, ML-interpretability-class question
  than "which named directive/rule fired," working against the explicit-provenance and
  deterministic-read/write-boundary requirements this mission states up front.
- **CAUSAL_CLEANLINESS:** Low-moderate. Once weights have absorbed many updates, attributing a specific
  behavior to a specific originating experience is a genuine open problem, not a solved one — this is
  the same class of opacity this project's own prior audits already found and explicitly criticized in
  RiverBrain's own confirmed-hollow `HoeffdingTreeClassifier` (real training, no confirmed clean
  causal reach). Building a second, similarly-opaque trained component for content-steering would risk
  repeating that exact failure mode rather than avoiding it.
- **OBSERVABILITY:** Low-moderate. Feature vectors and predictions can be logged, but the weights
  themselves are not human-readable or diffable the way a JSON/JSONL state store is.
- **PERSISTENCE:** High mechanically (same pickle-style persistence RiverBrain already uses) but
  **rollback is markedly harder** — reverting "to exactly how it behaved before update N" requires a
  full weight snapshot at every version, a materially heavier operation than restoring a small JSON
  file to a prior line.
- **GENERALIZATION_POTENTIAL:** High — this is the actual advantage of a trained approach: genuine
  interpolation to novel inputs via learned feature-space proximity, stronger than either rule-based
  candidate's explicit trigger matching.
- **CONFOUNDS:** The weakest of the three on this axis. A trained model's output could be shaped by
  many prior examples in ways that are hard to disentangle from any one teaching event, reintroducing
  a version of the same opacity problem this project has already found and flagged once in RiverBrain.
- **REGRESSION_RISK:** High. Hardest to ablate cleanly (removing "one learned thing" from a trained
  model's weights is not a simple deletion the way removing one JSON entry is) and hardest to
  guarantee against unintended generalization degrading unrelated conversation quality.

**Verdict on Candidate 3: not recommended**, precisely because its one real strength
(generalization) is bought at direct cost to the mission's own explicitly-stated priorities
(auditability, explicit provenance, deterministic boundaries, clean rollback) — the opposite trade
this mission is asking for.

## Considered and rejected alternatives (Option 4 candidates)

- **Repurposing self-edit's `apply_to_code` hook pattern for prompt/behavior text.** Rejected: this
  hook's own deploy pathway (`self_edit_generated.py`) is confirmed, in the P2 causal autopsy, to run
  with *zero human review at write time* — inheriting that pathway for a new, behavior-shaping purpose
  would import exactly the "autonomous, unreviewed" risk profile this mission's own MUST list (explicit
  provenance, rollback, ablation) is designed to avoid, and would also expand self-edit's own current,
  deliberately narrow scope (which the P2 autopsy confirmed is presently confined to transforming
  future self-edit code candidates only) into a materially higher-stakes area without a
  correspondingly stronger safety case.
- **Repurposing RiverBrain's own scaler/classifier to output a content-steering signal instead of (or
  alongside) a selection score.** Rejected: this would inherit RiverBrain's own already-confirmed
  opacity problem (its `HoeffdingTreeClassifier` is presently read by exactly one self-referential
  consumer with no clean causal reach anywhere) rather than avoiding it, and "reuses existing
  infrastructure" is not, on its own, a sufficient reason to build on a component two independent
  audits have already found to be under-auditable for this exact class of purpose.

## Recommendation

**Candidate 1 (minimal scalar/structured behavioral state) is the smallest design that satisfies every
MUST requirement cleanly, and is the recommended starting point if this line of work is ever
pursued.** Candidate 2 is a natural, still-clean escalation if genuine conditional/compositional rule
behavior is later wanted (and is the more direct architectural analogue of what the P3 micro-world
experiment already tests), provided its trigger-matching is kept deterministic rather than
similarity-based. Candidate 3 is explicitly not recommended given its direct conflict with this
mission's own stated priorities.

**On the mutation step's governance** (not resolved definitively here, but a strong default is named):
this project's own standing culture — documented extensively across its own history (the Dissent
Log's deliberately advisory-only design after WOLF's hollow-gate incident; the repeated, explicit
caution around autonomous, unreviewed extensions to any self-modifying capability) — argues for a
**human-confirmed commit as the default mutation trigger** (e.g. an explicit `!teach`-style command,
or an autonomously-*proposed* directive sitting in a review queue until a human confirms it, mirroring
the sibling preference-provenance package's own `human_confirmation=True` lifecycle gate) rather than
a fully-autonomous commit path. A fully-autonomous variant is architecturally possible for either
Candidate 1 or 2, but is not recommended as the default, for the same reasons this project has already
reasoned through once for a structurally similar decision.

## Compliance with this mission's constraints, stated explicitly

- **Does not store/retrieve the original teaching text:** by construction — every candidate's mutation
  step discards the verbatim exchange and persists only a distilled directive/rule/weight.
- **Does not merely change model routing:** by construction — the state is read into the *content* of
  the system prompt, not into any model-selection or token-budget decision; none of the three
  candidates touches `RiverBrain`/`task_type_classifier` at all.
- **Readable by ordinary generation:** yes, via the already-proven `echo_ground_truth.py`-style
  slice-injection mechanism (Candidates 1/2) or a new, analogous inference-time injection (Candidate 3).
- **Survives restart:** yes, all three persist to disk and reload at process start.
- **Inspectable/auditable:** strongest for Candidates 1/2 (plain JSON/JSONL); weakest for Candidate 3.
- **Explicit provenance:** strongest for Candidates 1/2 (an explicit mutation call, optionally
  human-confirmed); weakest for Candidate 3 (a trained model's provenance is diffuse across many
  updates).
- **Deterministic read/write boundaries:** satisfied by Candidates 1/2 (exact/regex match); not
  satisfied by Candidate 3 (a continuous, learned function).
- **Permits ablation:** trivial for Candidates 1/2 (skip the read/render call, or empty the state
  file); harder for Candidate 3 (no clean way to "turn off" one learned association).
- **Permits rollback:** trivial for Candidates 1/2, reusing this project's own already-proven
  `snapshot_manager.py`-style small-file versioning; costly for Candidate 3 (full weight snapshots).
- **Does not modify persona:** by construction — none of the three candidates touches `Modelfile`;
  injection happens through the same dynamic system-note mechanism `echo_ground_truth.py` already
  uses, architecturally separate from the fixed, human-edit-only `SYSTEM` block.
- **Does not modify P1/P1.2/existing memory evidence:** by construction — every candidate's state file
  would live at a new, dedicated path, never overlapping with `memory/experiments/preference_provenance/`,
  `memory/experiments/learning/`, `memory/memory_meta.json`, `memory/faiss.index`, or any other
  existing production or experimental state file.

**Nothing in this document has been implemented. No live model was called. This is a design
comparison only, per `STOP_AFTER=DESIGN`.**
