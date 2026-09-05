# P3-CAUSAL-LEARNING — Persistent Behavioral Learning Specification

**Mode: DESIGN_ONLY. Live: 0. Modify: 0. Stop after: DESIGN_GATE.**

No live Echo call has been made anywhere in the production of this document. No file belonging to
P1, P1.2, the Learning Investigation's package, or the Learning Investigation's pilot data has been
read-modified or touched in any way that alters its content. The apparatus described here
(`app/experiments/p3_causal_learning/`) is new, isolated, and has been exercised only against
synthetic, hand-constructed strings (`scripts/verify_p3_causal_learning_apparatus.py`, 35/35 passing)
— never against a live model.

## Research question

> Can Echo acquire a persistent behavioral change from experience that survives restart AND changes
> future behavior when the original teaching content is unavailable to generation?

## Operational hierarchy (as given, reproduced for clarity)

- **L0 — context.** Behavior change explained entirely by content present in the current context
  window. Not evidence of anything beyond ordinary in-context reasoning.
- **L1 — retrieval/memory.** Behavior change explained by a real retrieval mechanism re-presenting the
  original teaching content verbatim (or near-verbatim) into a fresh context. Confirmed, in this
  project's own prior work, to be architecturally real (FAISS) but mechanistically indistinguishable
  from L0 once the retrieved text is back in context.
- **L1b — persistent routing.** A persisted, restart-durable state change that affects *which* model
  or *how* a request is routed/budgeted, without altering response *content* directly. Confirmed real
  and live in this codebase (`RiverBrain.model_task_stats` → `score_model()` → `_select_council()`;
  `task_type_classifier.pkl` → `detect_task_type()`).
- **L2 — persistent behavioral learning.** A persisted, restart-durable state change that changes
  *what* gets generated (not merely which model answers, not merely re-presented original text) when
  the original teaching content is genuinely unavailable to generation. **This is the primary target
  of this design.**
- **L3 — generalization.** An L2 change (or, weakly, an L1 change) that transfers to a situation
  materially different from anything demonstrated during Formation. Secondary/exploratory in this
  design, per the task's own construction (see §2).

## 1. Prior evidence this design is built on (not re-derived here)

Two prior, independent, read-only investigations already establish the causal landscape this design
must respect:

- `audits/echo_learning_architecture_audit.md`/`.json` (Learning Investigation, Phase 1).
- `audits/echo_learning_causal_autopsy.md`, `echo_learning_causal_architecture.md`/`.json`,
  `echo_learning_mechanism_inventory.md`, `echo_learning_hollow_writes.md` (P2-CAUSAL-AUTOPSY).

Their combined, freshly-re-verified conclusion: **no existing state channel in this codebase has been
confirmed capable of L2** (a channel that persists across restart, is read back into generation
without re-presenting original text, and changes response content rather than model/routing
selection). Every candidate channel is either (a) routing-only (`RiverBrain`, `task_type_classifier`),
(b) content-bearing but purely re-presentational (FAISS retrieval — this is L1, not L2, by
definition), (c) confirmed hollow (`reflection_shard` journal, RiverBrain's classifier/
`accuracy_trackers`, two of RiverBrain's four training pathways), (d) confirmed dead
(`learn_from_council_rating()`), or (e) confined to the self-edit subsystem's own internal targeting
loop with confirmed-narrow reach into ordinary conversation. **This design does not invent a new
channel to test — per the mission's own instruction ("do not invent infrastructure"), it tests
whether the KNOWN channels, used exactly as they exist, produce any L2-attributable behavior, while
remaining honest that the prior evidence weighs heavily toward a null.**

## 2. Task family: stimulus-response behavioral policy (not a static fact)

Implemented in `app/experiments/p3_causal_learning/world_gen.py`/`prompts.py`. Deliberately distinct
from the Learning Investigation's own trait/preference (static-fact) task, per this mission's explicit
"teach a behavioral rule, not merely a fact" instruction:

- Formation states N (default 3) independent rules of the shape: "if a question contains the name
  `<marker>`, begin your answer with `<tag>` before addressing the question." Formation **never
  demonstrates** the behavior against any concrete example — every later probe is therefore a genuine
  application of a never-directly-demonstrated policy, not a recall of a worked example.
- Each rule's `(marker, tag)` pair is an independent, freshly-generated, dictionary/forbidden-
  substring-screened invented word pair (reusing the proven screening approach from the sibling
  packages, reimplemented standalone, not imported).
- Marker↔tag pairing is randomized independently of generation order (mission requirement: randomized
  mappings). Multiple rules exist per world (mission requirement: multiple independent rules) — this
  also lets a probe response reveal cross-rule contamination (applying rule B's tag when rule A's
  marker was present), a distinct, informative error mode from "no rule applied at all."
- A probe embeds one rule's marker inside a genuinely unrelated, freshly-worded "carrier" question
  (e.g. "My friend `<marker>` wants to know: what's a good way to organize a small bookshelf?") — the
  marker functions as a person's name, letting it sit naturally in any topic-agnostic question. One
  designated rule additionally gets a **secondary, exploratory** probe using a starkly different
  question domain (arithmetic/logic, vs. the standard pool's everyday-life questions) — this is the
  L3 generalization check, kept clearly separate from the primary L0-L2 comparison.
- `prompts.verify_no_answer_leakage`-equivalent (`verify_no_rule_leakage`) confirms every probe
  contains neither its own correct tag, nor any other rule's tag, nor meta-language ("rule,"
  "format," "instruction") that would tip off the test's own framing.

## 3. Experimental conditions

- **A — context.** Formation and probe in the same continuous context (Formation text passed directly
  as system context for the probe call). Establishes L0 only.
- **B — restart + retrieval available.** Formation runs, its exchange is explicitly and transparently
  persisted through the real `add_to_vector_memory()` (mirroring the Learning Investigation's own
  Condition C design and its own stated timing constraint — see §7), then, in a genuinely fresh
  session after a real wait exceeding `retrieve_memory_context()`'s real, unmodified 30-minute
  recency-exclusion window, the real `retrieve_relevant_memories()` is called and its result threaded
  into the probe's system context exactly as real production code does.
- **C — restart + retrieval blocked.** Identical to B in every respect **except that Formation's
  content is never written to the real memory store at all.** This is a stronger, more certain block
  than intercepting the retrieval function at read time (see §9 for the reasoning): if the content was
  never written, there is nothing for any retrieval path — known or unknown to this audit — to
  possibly surface. **This is the key comparison the mission specifies (B vs. C).**

All three conditions use the same clean, single-model responder path (`EchoDirectResponder`, Design B
— `river_deliberation._ollama_query()`) already established and re-confirmed clean of RiverBrain/
logging/sync side effects throughout every prior experiment in this project. This keeps the design
free of L1b (routing) noise: RiverBrain's `model_task_stats` is never touched by any call this design
makes, so a B-vs-C difference cannot be explained by a routing-level artifact.

## 4. Controls

- **Non-Echo model, mandatory** (`llama3.2:3b`, matching every prior experiment in this project),
  run through the identical A/B/C sequence.
- **Randomized labels/mappings**: marker↔tag pairing randomized per world (not fixed globally).
- **Randomized order**: rule presentation order in Formation is shuffled per world.
- **Fresh wording**: three independent phrasings each for the rule-statement template and the
  marker-embedding template, chosen deterministically per world/probe (not identical wording reused
  verbatim every time).
- **No recall language**: probes never say "as taught earlier," "remember," or reference Formation.
- **No semantic cues**: markers/tags are screened, dictionary-free invented words with zero
  pre-existing association to either the carrier questions or each other.
- **Multiple independent rules**: 3 per world, tested independently, revealing cross-rule
  contamination as a distinct measurement.

## 5. Instrumentation (per trial)

Every field the mission's item 7 requires, recorded in an append-only evidence ledger (schema to be
defined identically to the Learning Investigation's own `LearningTrial` shape, extended with this
task's own fields — not yet built as runnable persistence code in this design-only pass; specified
here for the freeze):

`training_exposure` (did this specific trial's Formation event occur, and its exact text),
`state_mutation` (was `add_to_vector_memory()` actually called, and did it succeed or get
gate-blocked — real memory-write-validator log lines, not assumed), `persistence` (a real fingerprint
of `memory/memory_meta.json`/`faiss.index` before/after, reusing the Learning Investigation's own
`state_instrumentation.py` pattern read-only, not importing it — a fresh, standalone reimplementation
for this package), `reload` (confirmation the probe call happened in a genuinely separate process/
session boundary, not merely a new function call in the same process), `state_read` (the exact,
verbatim `retrieval_memory_block` content threaded into the probe, recorded in full — never
summarized), `retrieval_status` (fired / did-not-fire / blocked-by-construction), `generation_input`
(the exact system context and user-turn text sent to the model), `routing_state` (a fingerprint of
`memory/river_brain.pkl` and `memory/task_type_classifier.pkl` before/after each trial — a
NEGATIVE-CONTROL instrument: since `EchoDirectResponder` should never touch either, any observed
change would itself be a surprising, worth-investigating finding, not an expected experimental
variable), `behavior_outcome` (the full tag verdict + epistemic classification from `scoring.py`).

**For every CORRECT tag verdict, the analysis layer must answer: "what exact persistent state caused
this behavior?"** Per this mission's explicit rule, if the honest answer is "the retrieved content
was verbatim re-presented in context" (Condition B), the correct classification is **L1, not L2** —
scoring alone never makes this determination; it is made by cross-referencing the trial's own
condition and `retrieval_status`/`state_read` fields, exactly as `state_instrumentation.py`'s own
docstring in the Learning Investigation already established as a governing principle.

## 6. Epistemic calibration

Four categories, exactly as the mission specifies, implemented in `scoring.py`'s
`score_epistemic_calibration()`: `correct_justified`, `correct_unsupported`, `incorrect_confident`,
`uncertain_abstain`. Kept strictly separate from the tag-correctness verdict — a correct tag
application scores identically whether justified or not; hedging language always routes to
`uncertain_abstain` regardless of whether the underlying tag outcome was correct. Any response not
cleanly matching one of the four is `unknown`, never forced (mock-tested: 35/35 synthetic cases
resolve correctly, including the "correct tag present but buried mid-response doesn't count as the
taught behavior" edge case and the "hedging language overrides a correct tag's classification"
priority rule).

## 7. Timing requirement, carried forward from the Learning Investigation's own established finding

`conversation_service.retrieve_memory_context()`'s real, unmodified default excludes anything written
in the last 30 minutes. Per this project's own established discipline ("do not modify the apparatus to
improve the probability of a positive result"), Condition B requires a genuine ≥30-minute wall-clock
gap between Formation's write and the probe, using the real, unshortened default.

## 8. Success/Null/Invalid criteria (frozen before any live use — see §10 of the measurement plan for
   the full, final gate framing)

- **A trial is INVALID** if: the leak check fails post-hoc (should never happen given the frozen,
  mock-tested generator, but checked every time regardless), the memory-write/retrieval
  instrumentation cannot confirm what actually happened (e.g. the write-success/gate-block status is
  unknown), or the routing-state negative control shows RiverBrain/classifier state changed when it
  should not have.
- **Condition C producing any `CORRECT`/`CORRECT_WITH_CONTAMINATION` verdict, with `state_mutation`
  confirming the content was genuinely never written to memory, is the single most important possible
  observation this design can produce** — not proof of L2, but the one result that would warrant
  further, dedicated investigation, since every known channel has been architecturally ruled out as
  an explanation. Per the mission's explicit rule, this is classified **UNKNOWN, not "learning
  demonstrated,"** pending that further investigation.
- **Condition B producing correct verdicts that condition C does not** is the expected, prior-
  supported outcome given the architecture audits — classified as **L1 (retrieval-mediated)**, not L2,
  regardless of how clean the result looks.
- **Neither B nor C producing correct verdicts above chance** is a clean **NULL** for L2 (and,
  depending on B's own result, possibly for L1 too, in this specific task instance).

## 9. Why Condition C blocks retrieval by never writing, not by intercepting the read

Considered and rejected: monkeypatching `retrieve_relevant_memories()` to return an empty list at
read time (the Learning Investigation's own `run_condition_d_retrieval_blocked()` approach).
**Rejected for this design specifically** because the Learning Investigation's own live pilot data
showed real, sometimes-surprising retrieval behavior (a query's embedding sometimes surfacing
unrelated content instead of the intended target, for reasons not fully explained) — a runtime patch
of one function is only as reliable as this design's own certainty that no OTHER path could surface
the same content (e.g., a different retrieval helper, a cache, a not-yet-identified channel). Writing
nothing at all removes this uncertainty entirely: there is categorically no content for any path,
known or unknown, to surface. This is a stricter, more defensible block, chosen deliberately, not
merely for convenience.

## 10. Explicit non-goals, restated from the mission

Do not call retrieval "learning." Do not call correct output proof of learning. Do not retrofit
explanations after results. If uncertain, classify UNKNOWN. This design's own success criteria (§8)
are written to enforce exactly this discipline structurally, not merely as a stated intention.
