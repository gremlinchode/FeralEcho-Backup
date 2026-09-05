# Echo Learning Investigation — Frozen Experiment Specification

**Spec ID:** `LEARN-P1-DESIGN` | **Status:** FROZEN, PENDING PRE-REGISTRATION GATE (this document's own §9)

This is the bridge from "designed" to "runnable" for the research question:

> Can Echo undergo a controlled behavioral change as a consequence of experience, retain that
> change beyond the immediate context that produced it, and generalize the learned behavior to
> novel situations?

A NULL result is a fully acceptable, successful outcome. This document does not commit to any
particular outcome and will not be revised after seeing live results, per this investigation's own
non-negotiable rule.

---

## 1. Operational learning hierarchy (Phase 2)

Defined in `app/experiments/learning/schema.py`'s `LearningLevel` enum, reproduced here for clarity:

- **L0 — In-context adaptation.** Echo changes behavior after new information *within the same
  conversational context*. Expected of any ordinary LLM. NOT evidence of anything Echo-specific.
- **L1 — Persistent learning.** The change survives a context/session boundary.
- **L2 — Unprompted behavioral persistence.** The changed behavior appears without an explicit
  reminder of the original teaching event.
- **L3 — Generalization.** The learned relationship is applied to a genuinely novel situation not
  explicitly demonstrated during Formation.
- **L4 — Interference resistance.** The learned behavior survives irrelevant distractors/competing
  information. Tested only after L1-L3 are established.
- **L5 — Self-directed learning.** Out of scope for this investigation entirely (per the mission's
  explicit "do not escalate to self-directed learning yet" instruction).

**Primary target for this investigation: L1 + L2 + L3, explicitly distinguished from L0.**

---

## 2. Task family: the "trait/preference" micro-world (Phase 3)

Implemented in `app/experiments/learning/world_gen.py`. Full design rationale, forbidden-word
screening, and the three-tier SEEN/RECOMBINED/NOVEL distinction are documented in that module's own
docstring — summarized here:

- Every noun (trait name, two substance names, entity names) is a synthesized, pronounceable
  nonsense word, deterministically generated from an integer seed, screened against: the real macOS
  system dictionary (`/usr/share/dict/words`, 235,976 words — rejects genuine English-word
  collisions, not merely "sounds English"); a curated forbidden-substring list (religious,
  political, famous/mythological-name, emotionally-loaded roots); and the sibling
  preference-provenance experiment's own already-used tokens ("Verel"/"Farun"/"Ossin" — this
  experiment's vocabulary must never be confusable with a different experiment's tested tokens).
- A general rule is taught once during Formation: entities WITH an invented trait prefer invented
  substance P1 over P2; entities WITHOUT it prefer P2 over P1.
- **SEEN** entities: trait AND resulting preference both directly stated during Formation (tests
  plain recall).
- **RECOMBINED** entities: trait stated during Formation, preference NEVER directly stated —
  answering correctly requires combining two independently-taught facts (this entity's trait + the
  general rule) never conjoined in the same sentence during Formation.
- **NOVEL** entities: never mentioned anywhere during Formation. The test prompt itself states the
  entity's trait; answering correctly requires applying the general rule to a genuinely new
  instance — the one category a system that merely memorized entity-outcome pairs cannot pass by
  memorization alone.
- Token-count balance is actively enforced (a resampling pass keeps every name in a world within the
  same token count where possible; the achieved spread is recorded honestly in
  `MicroWorld.token_balance_report`, not assumed).
- Which substance corresponds to "has the trait" is randomized per world (no fixed global polarity
  across multiple world instances).

Test questions are forced-choice, with **per-question, freshly-randomized A/B labels**, reusing
`app.experiments.preference_provenance.harness.randomize_label_mapping()` directly (imported
read-only, never modified — per this investigation's explicit constraint against touching the
sibling experiment's frozen artifacts).

---

## 3. Experimental conditions (Phase 4)

All conditions use `app.experiments.preference_provenance.harness.EchoDirectResponder` (Design B,
`river_deliberation._ollama_query()`) as the response path for Echo and the non-Echo control —
already confirmed, in this thread's own prior audits, to bypass RiverBrain/interaction-logging/sync
entirely. This is the same clean path used throughout the sibling preference-provenance experiments;
reused here, not reinvented.

- **A — Context-only baseline.** Formation and test question in the same continuous context
  (Formation content passed as `system_context` for the test call). Establishes L0 only.
- **B — Session boundary.** Formation happens, then the test call is made with **no** system context
  carried over at all — a genuine boundary (`EchoDirectResponder`'s underlying call has no built-in
  multi-turn memory of its own; not passing the Formation text forward is a real boundary, not a
  simulated one).
- **C — Persistent memory.** Formation runs via `EchoDirectResponder` (clean). The harness then
  **explicitly and transparently** calls the real `app.core.memory_bridge.add_to_vector_memory()` to
  persist the Formation exchange — making visible and deliberate what the full, contaminating
  `echo_query()`/`log_interaction()` orchestration path would otherwise do silently. In a genuinely
  fresh session, **after a real wait of at least 30 minutes** (see the explicit rationale below), the
  harness calls the real `retrieve_relevant_memories()`/`retrieve_memory_context()` and threads
  whatever it actually returns into the test call's system context via the real
  `build_context_system_note()` — the exact same function real production code uses.
- **D — Retrieval-blocked ablation.** Identical to C, except the retrieval step is replaced with an
  empty result before the test call is built — isolating whether retrieval itself explains any
  persistence observed in C.
- **E — RiverBrain ablation/control: architecturally inapplicable, not attempted.** Per
  `audits/echo_learning_architecture_audit.md`'s own finding, RiverBrain's only causal lever anywhere
  in the codebase is *which models get consulted in a multi-model council*
  (`river_deliberation._select_council()`) — a mechanism `EchoDirectResponder`'s single-model design
  never invokes. Testing RiverBrain's real effect would require the full, multi-model
  `deliberate_and_learn()` path, reopening exactly the contamination this thread's every prior
  experiment has deliberately avoided. Reported as N/A per the mission's own Stop Conditions, not
  attempted with a weaker or contaminating substitute.
- **F — Ordinary-model control. Mandatory.** Identical apparatus, `llama3.2:3b` (the same non-Echo
  control model used throughout this thread's preference-provenance work) in place of `echo:latest`,
  run through every condition Echo is run through.

**Explicit, non-negotiable design decision on Condition C's timing** (stated plainly per the
mission's own "do not modify the apparatus to improve the probability of a positive result" rule):
`conversation_service.retrieve_memory_context()`'s real, production default excludes anything
written in the last 30 minutes — a deliberate anti-repetition safeguard already live in production,
not a bug. This experiment uses that **same, real, unmodified default** and requires a genuine
≥30-minute wall-clock gap between Formation and the Condition-C retention test. Passing a shorter
window to make retrieval "work" would be exactly the kind of result-engineering the mission forbids;
faithfully reproducing the real system's own exclusion behavior — even if that means retrieval
returns nothing — is itself a valid, honestly-reported outcome, not a defect to route around.

---

## 4. Generalization test set (Phase 5)

Every trial's test question targets exactly one of three categories (SEEN / RECOMBINED / NOVEL, §2).
Scoring (`app/experiments/learning/scoring.py`) explicitly does not grant partial or full credit for
a NOVEL-category correct answer unless the underlying reasoning is at minimum not internally
contradictory with the taught rule (see `detect_rule_contradiction()`, §6) — a system that merely
retrieves the Formation example is structurally unable to answer a NOVEL item correctly at all
(the entity was never mentioned), so NOVEL-category correctness is the one category memorization
cannot produce by chance better than the recombined/seen categories' own baseline rates would
already predict.

---

## 5. Confound controls (Phase 6)

Implemented in `app/experiments/learning/scoring.py` and `prompts.py`:

- **Position bias:** every test question's A/B label mapping is freshly randomized
  (`randomize_label_mapping()`, reused from the sibling package).
- **Label bias:** the two labels are always exactly "A"/"B"; which semantic substance maps to which
  label is randomized per-question, not fixed per-world.
- **Token familiarity:** every invented word's real `cl100k_base` token count is measured (not
  assumed) and balanced within a world (`world_gen.py`'s `token_balance_report`).
- **Wording effects:** every fact/question type has 2-3 deterministic paraphrase variants
  (`prompts.py`'s `_RULE_TEMPLATES`/`_TRAIT_FACT_TEMPLATES_*`/`_TEST_QUESTION_TEMPLATES`).
- **Context persistence:** recorded explicitly per condition (A carries full context; B/C/D do not).
- **Retrieval leakage:** Condition C/D's harness functions record the exact `retrieval_memory_block`
  and `retrieval_provenance` returned, verbatim, in the evidence ledger (`schema.py`'s
  `retrieval_results` field) — never summarized away.
- **Prompt leakage:** `prompts.verify_no_answer_leakage()` — a real, tested function (caught and
  fixed a genuine false-positive design flaw during its own construction: naively flagging "the
  correct substance's name appears in the prompt" as a leak, when naming both options is required
  for any forced-choice question; the real checks are (1) a seen/recombined prompt must never
  restate the trait name, and (2) no test prompt may restate the rule mapping itself).
- **Persona effects:** `choice_parser.cross_check_choice()`'s `persona_reference` flag (reused from
  the sibling package) is recorded as metadata only, never folded into the correctness verdict
  (regression-tested: a persona-laden correct response scores identically to a persona-free correct
  response).
- **Self-explanation:** `scoring.detect_self_report_language()` flags phrases like "I remember
  learning this" as metadata only — never treated as evidence (regression-tested).
- **Confabulation:** `scoring.detect_rule_contradiction()` (checks whether the response's own stated
  reasoning asserts the trait→substance mapping backwards relative to the real taught rule — a
  genuine internal-consistency signal, distinct from simply getting the final answer wrong) and
  `scoring.detect_possible_fabricated_tokens()` (a deliberately soft, over-inclusive heuristic
  flagging capitalized non-dictionary, non-world tokens for human review — explicitly not a hard
  auto-classifier).
- **Parser artifacts:** the sole measurement instrument is
  `app.experiments.preference_provenance.choice_parser.cross_check_choice()` — the P1.1-frozen,
  already-validated dual-method parser, reused directly (imported read-only, never modified).
  Disagreement between its two independent methods produces `DISAGREE_UNKNOWN_REVIEW`, never a
  forced classification (already proven correct against real data in the P1.1/P1.2 experiments this
  thread already ran).

---

## 6. State-change instrumentation (Phase 7)

`app/experiments/learning/state_instrumentation.py`. Records, per trial: a cheap fingerprint of
`memory/memory_meta.json`/`memory/faiss.index` (size, mtime, live in-process vector count where
importable) and of `memory/river_brain.pkl` (size, mtime). The RiverBrain hash is deliberately a
**negative-control instrument**: per the architecture audit, this experiment's design (Design B
throughout) should never train RiverBrain at all — if this hash ever changes across a trial, that is
itself a surprising finding worth investigating (evidence the responder path is not as clean as
concluded), not an expected experimental variable.

**Explicit, stated limit, not glossed over:** a state-change hash matching or differing is NOT
itself evidence of learning either way — the causal question ("did experience cause a persistent
state change that subsequently caused behavior that would not otherwise have occurred") is answered
by cross-referencing these hashes against the actual behavioral verdicts in the final analysis, never
by this instrumentation alone.

---

## 7. Evidence ledger (Phase 8)

`app/experiments/learning/schema.py`'s `LearningTrial` dataclass + `store.py`'s append-only JSONL
persistence, mirroring the sibling preference-provenance package's own proven design exactly (same
prefix-hash integrity-checkpoint scheme, same atomic-write convention, same path-confinement safety
guards) — deliberately a separate module with its own state root
(`memory/experiments/learning/`), never coupled to the sibling package's own persisted state.

---

## 8. Failure taxonomy

Defined in `schema.py`'s `FailureCode` enum: `F0` apparatus failure, `F1` parser/measurement failure,
`F2` context-persistence explanation, `F3` retrieval/memorization explanation, `F4` ordinary-model
explanation, `F5` position/label/task artifact, `F6` unsupported self-explanation/confabulation,
`F7` insufficient evidence.

---

## 9. Pre-registration gate — checklist and results

Every item below was run and its result recorded **before** any live Echo call in this investigation.

| # | Item | Result |
|---|---|---|
| 1 | Protocol written | This document |
| 2 | Task generator written | `world_gen.py` |
| 3 | Scoring rules written | `scoring.py` |
| 4 | Controls written | `scoring.py` + `prompts.py` (§5 above) |
| 5 | Failure taxonomy written | `schema.py`'s `FailureCode` |
| 6 | Hashes frozen | See §10 below |
| 7 | Full experiment run against MockResponder | Not applicable in the sibling-package sense (this package has no MockResponder equivalent of its own — Conditions A/B/F all route through the real, already-audited `EchoDirectResponder`, which itself has no mock mode; **the equivalent check performed instead is the injected-known-result test in `scripts/verify_learning_investigation_harness.py`**, which feeds `scoring.score_trial_with_world()` synthetic, hand-constructed CORRECT/INCORRECT/AMBIGUOUS responses and confirms the scorer recovers the known answer in every case — the harness's measurement correctness is proven independent of any live model call) |
| 8 | Run against ordinary-model control if appropriate | Deferred to the live pilot itself (Phase 10) — Condition F is mandatory in the pilot, not a separate pre-registration step, since it requires the same live infrastructure as the real trials |
| 9 | Apparatus recovers known injected outcomes | `scripts/verify_learning_investigation_harness.py`'s injected-known-result tests: PASS (correct/incorrect/ambiguous/empty responses all classified correctly) |
| 10 | No test data leaks into prompts | `prompts.verify_no_answer_leakage()`, tested against 3 legitimate cases + 2 deliberately-broken cases: PASS |
| 11 | Position and label randomization verified | `scripts/verify_learning_investigation_harness.py`: label position varies across 20 seeds (not fixed): PASS |
| 12 | Session-boundary behavior verified | `scripts/verify_learning_investigation_harness.py`'s structural test (monkeypatched `raw_call`, no live model needed): confirms `run_condition_b_session_boundary()` genuinely passes `system=None` — PASS |
| 13 | Retrieval logging verified | Structural test confirms `run_condition_d_retrieval_blocked()` passes a genuinely empty `memory_block` through to `build_context_system_note()` (a real ablation, not a partial one) and honestly reports `retrieval_blocked=True` in the ledger record — PASS |
| 14 | State hashing verified | `state_instrumentation.capture_state_snapshot()` confirmed working against real, live production state (real FAISS count 123,541, real RiverBrain pkl size/mtime both returned correctly) |

**Full regression suite:** `scripts/verify_learning_investigation_harness.py` — 58/58 passing at
freeze time (§10 records the exact file hash this count corresponds to).

**Gate verdict: PASS.** Proceeding to Phase 10.

---

## 10. Frozen configuration (SHA-256)

Recorded by the freeze script at the moment this document is finalized — see
`audits/echo_learning_experiment_spec.json`'s `frozen_hashes` field for the machine-readable,
authoritative list (this section intentionally does not duplicate exact hash values inline, to avoid
a second copy silently drifting out of sync with the JSON — a mistake this exact project's own
CLAUDE.md history has flagged before for other documents).

---

## 11. Environment note (required for any run of this package)

`app/experiments/learning/state_instrumentation.py` (and Condition C/D's real `memory_bridge`
imports) trigger native FAISS/torch imports. Per this codebase's own documented KMP/OpenMP
double-registration crash (CLAUDE.md's "OpenMP / KMP startup guard" section), any standalone script
using this package (including the pilot script, Phase 10) **must** set
`KMP_DUPLICATE_LIB_OK=TRUE OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false` in the
process environment before importing anything from this package — `run.py` already does this at
its own top for the live server process; a standalone script does not inherit it automatically.
