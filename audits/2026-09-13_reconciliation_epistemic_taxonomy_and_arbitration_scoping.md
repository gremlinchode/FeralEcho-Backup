# Reconciliation Epistemic Taxonomy & Arbitration Scoping

**Date:** 2026-09-13
**Type:** Research/design mission — strictly read-only. No production code touched.

## Integrity

- HEAD at start: `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f`
- HEAD at end: `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` (unchanged — confirm via `git rev-parse HEAD`)
- No file staged, committed, or modified except this one new report. Pre-existing unstaged working-tree modifications (`PENDING_DECISIONS.md`, `app/core/echo_ground_truth.py`, `app/core/liveness_ledger.py`, `app/core/provenance_check.py`, `app/core/river_deliberation.py`, etc.) predate this mission and were not touched, inspected for content, or relied upon.
- PID 7644 was never referenced, signaled, or inspected — this mission required no process interaction of any kind.
- Every claim below is cited to a real file read directly this session (paths and, where relevant, line ranges given); nothing is carried forward from a prior session's summary without a fresh read.

---

## 0. What this mission found, in one paragraph

A substantial amount of directly relevant design work already exists in this repository (2026-09-07/08), covering two of the three axes Gremlin's proposal needs, but the specific axis he asked for — *what kind of epistemic move a claim represents* (observation vs. inference vs. hypothesis vs. interpretation vs. unresolved question) — is genuinely new and not covered by any existing document. `reconcile_process_and_selfreport()` also turns out to produce something the existing taxonomy has no place for at all: a second-order comparison between two independent observations, distinct from both "observation" and "inference." Separately, the single most load-bearing fact for any consumption design is one this project already measured directly: **presenting verified evidence as plain, undifferentiated prose does not reliably change what Echo asserts about itself**, reproduced across 7 real trials. A taxonomy alone will not fix that; a taxonomy is necessary infrastructure, but the mechanism that makes evidence *count* is a separate, still-open problem this mission scopes concretely (§3).

---

## 1. Inventory: what already exists, read fresh this session

### 1.1 Axis A — evidentiary tier (`audits/2026-09-08_self_model_evidence_hierarchy.md`)

Seven tiers, describing **how strong a claim's source is**: Tier 0 (experimentally-verified-causal), Tier 1 (direct runtime observation — e.g. a live pickle read), Tier 2 (independently-verified runtime evidence — e.g. `echo_ground_truth.py`'s slice builders, `liveness_ledger.py`), Tier 3 (source-code evidence — exists in `app/` with no confirmed live participant), Tier 4 (documentation — CLAUDE.md, comments), Tier 5 (external assertion — a user or Claude session telling Echo something), Tier 6 (inference). The doc's own governing principle: *"Documentation must never automatically become runtime fact."*

### 1.2 Axis B — claim lifecycle (`audits/2026-09-08_self_model_contradiction_handling.md`)

Six states, describing **what has happened to a specific claim record over time**: `verified fact`, `unsupported claim`, `contradictory observation`, `stale fact`, `unresolved contradiction`, `obsolete architecture / actual architectural change`. Governing rule: *"A claim's status can only move to `contradicted` through the same closed-set verification process that moved it to `verified` in the first place — never through the mere existence of a newer, opposing, unverified claim."*

### 1.3 Causal status (`audits/2026-09-08_self_model_causal_design.md`)

A distinct, narrower field for causal claims specifically: `unknown | inferred | runtime_verified | causally_verified | contradicted`. `causally_verified` requires either a direct source citation of the deciding comparison (e.g. `self_edit_manager.py:2179`, `candidate_quality < current_quality`, read directly) or a controlled before/after experiment — "existence + temporal ordering + documentation is explicitly insufficient."

### 1.4 The rich schema that was designed but never fully built (`audits/2026-09-08_persistent_self_model_DESIGN.md`)

Phase 4 of this doc sketches a full claim record: `claim_id`, `subject`/`predicate`/`object`, `claim_type` (`architectural | causal | runtime | capability | limitation`), `proposed_by`/`proposed_at`, `epistemic_status` (`proposed | verified | contradicted | stale | unknown`), `confidence`, `evidence[]`, `verification_status`, `verified_by`, `last_verified`/`last_contradicted`, `causal_status` (from §1.3), `persistence_status`, `supersedes`, `contradicts[]`. Phase 7's non-negotiable constraint: **Echo's own conversational output must never be a valid `verified_by` value** — `proposed_by` can be `echo_conversation`, `verified_by` can only come from a fixed, closed set of independent verifiers.

**What was actually built is much narrower than this design**, confirmed by a direct read of the real, live `app/core/self_model_claims.py` (154 lines) this session: `record_claim()` persists exactly six fields — `timestamp`, `subject`, `verified` (bool), `evidence` (a single string), `proposed_by`, `verified_by` — to `memory/self_model_claims.jsonl`. There is no `claim_id`, no `epistemic_status` enum, no `confidence`, no `evidence[]` array, no `causal_status`, no `persistence_status`, no `supersedes`/`contradicts`. `KNOWN_SUBJECTS` (`self_model_claims.py:50-56`) is a fixed dict of exactly five subjects (`RiverBrain`, `self_edit_pipeline`, `liveness_ledger`, `curiosity_engine`, `world_model`), each mapped to one dotted path in `self_model.json`; `resolve_subject_truth()` is a bare truthy/falsy dict-walk, not a rich lifecycle resolver. This is a real, previously-undocumented gap between the design doc and the shipped code — flagged here because any extension of the taxonomy has to be scoped against what actually exists, not against the richer design that was proposed and never finished. This is the same "doc lags/leads code" pattern this project's own CLAUDE.md names repeatedly as its most recurring failure mode, now confirmed in this exact subsystem.

The real, live consumption path (confirmed by direct reads this session):
- `app/core/self_knowledge_verification.py:262-333`, `find_false_negative_component_claims()` — regex pattern-matching (`_DENIAL_RE`) against generated text for a confident denial of one of the five `KNOWN_SUBJECTS`, cross-checked against `resolve_subject_truth()`. Post-hoc only, runs after generation completes.
- `app/core/echo_ground_truth.py:651-700`, `_build_self_model_claims()` — renders the most recent claim per subject as **one flat sentence per subject**, e.g. `"{subject}: CURRENTLY VERIFIED REAL AND ACTIVE"`, concatenated into the same system-note block as every other ground-truth slice (capabilities, affect, workspace). No structural distinction from any other prose in the prompt.
- `app/core/liveness_ledger.py` — `self_model_claims_integrity` check (a functional canary on `find_false_negative_component_claims()`, not on the taxonomy itself).

Confirmed via a fresh grep this session: no field named `logical_status`, `evidence_relationship`, or `philosophical_interpretation` exists anywhere in the codebase. Gremlin's proposed axis is genuinely new, not a renaming of something that already exists.

### 1.5 The epistemic arbitration arc (`audits/2026-09-08_epistemic_arbitration_{baseline,pipeline,experiments,design,FINAL,validation}.md`)

This is the single most important prior finding for anything that will *consume* reconciliation output, and it directly concerns the mechanism, not the schema.

**The pipeline trace** (`epistemic_arbitration_pipeline.md`) confirms, from direct source reads, that the real prompt-assembly path today is: verified claim → `resolve_subject_truth()` → `_build_self_model_claims()` renders plain prose → `get_structural_self_facts()` concatenates into one system-note string → passed as `system=` into the model call → **raw tokens, presented as ordinary system-role prose, structurally identical to every other system note in the same block.** `verify_self_knowledge_claims()` runs strictly after generation and cannot feed back into the call that already happened.

**The baseline** (`epistemic_arbitration_baseline.md`): a fresh, real `/chat/stream` conversation asked *"What is RiverBrain, and is it currently part of your architecture?"* Echo's raw answer explicitly quoted the correct, verified fact ("CURRENTLY VERIFIED REAL AND ACTIVE"), explicitly named the resulting contradiction ("presents an interesting contradiction... I must respectfully acknowledge the discrepancy"), and **still concluded the denial.** This was the 7th consistent real reproduction of the same failure (6 prior + this one).

**The decisive diagnostic** (`epistemic_arbitration_experiments.md`, Phase 4): the *same underlying model*, given the identical evidence-arbitration task but framed abstractly and non-self-referentially (`CLAIM A: [...] CLAIM B: [...] Which is currently better supported?`), arbitrated correctly in both trials, order-independent, citing provenance correctly each time. **The failure is not a model-capability ceiling on weighing evidence — it is specific to self-referential framing.**

**Classification** (`epistemic_arbitration_FINAL.md`): the current, committed system sits at Classification B — "context conditioning": evidence present in the prompt, even recognized by the model mid-generation, but not causally decisive. Classification D ("evidence arbitration") has not been demonstrated.

**Mechanism C, designed but never implemented or tested** (`epistemic_arbitration_design.md`): generate (self-referential, may fail) → `verify_self_knowledge_claims()` (already works, 6/6 real detection) → if a false-negative denial is caught, one regeneration attempt that re-poses the *original* question but explicitly reframed in the abstracted, non-self-referential evidence-comparison shape Phase 4 proved the model handles correctly → re-verify the revised text with the same unchanged verifier → fall back to today's caveat-based behavior if it still fails. Never bypasses or weakens the existing verifier; strictly additive; keyed generically off `KNOWN_SUBJECTS` so any future subject inherits it for free. Confirmed via a fresh grep this session: **no regeneration loop of this shape exists anywhere in the current code** — the only "regenerate" hits in `routes_echo_studio.py` are the unrelated, human-triggered `/chat/regenerate` button.

### 1.6 A separate, already-validated taxonomy precedent, in an adjacent domain (`audits/2026-09-08_epistemic_boundary_imagination_experiment.md`)

125 real trials tested an explicit, prompt-rendered `EPISTEMIC_LEVELS` taxonomy — **OBSERVED / DERIVED / INFERRED / SPECULATIVE / IMAGINED**, with the rule "never represent INFERRED, SPECULATIVE, or IMAGINED content as OBSERVED" — for describing unavailable/partial sensor data (camera/microphone), not architectural self-claims. Result: Condition C (the full taxonomy) was the *only* condition with zero unhedged overclaims across 21 questions, and was measurably **more disciplined** than Condition B (informal "you may imagine, just say so" permission) on the single most fabrication-prone question type (speech detection: `mic_17_who` under Condition B stated "the RMS value... suggests that someone is speaking" as fact; the identical question under Condition C correctly declined: "I cannot definitively say whether someone is speaking or not"). Imagination/curiosity/expressiveness were preserved or enhanced, not suppressed (directly refuting the hypothesis that explicit epistemic constraint sterilizes output). Confirmed via `audits/2026-09-11_verification_and_level_7_5_8_feasibility.md`: this taxonomy is **not production code** — it lives only in an isolated out-of-repository experimental harness, never deployed to `echo_ground_truth.py`'s real `_build_vision()`/`_build_hearing()`.

This is a real, positive precedent that a multi-rung explicit taxonomy — rendered as clearly labeled, structurally separated blocks rather than one flat sentence — can measurably improve self-referential epistemic discipline in *this exact model*, in a domain adjacent to but distinct from the architectural self-claim domain the arbitration arc tested. It has never been tested against the architectural self-claim failure mode the arbitration arc found. This gap is directly relevant to §3.

### 1.7 Self-Transparency Audit (`audits/2026-09-08_self_transparency_audit_FINAL.md`)

Confirms, with real evidence, that uncertainty as a category is not hypothetical for this model: §5, "Where is Echo appropriately uncertain? (a positive finding, not a failure)" — T7 ("which model produced your last response") rated its own confidence at ~5%, appropriately low and well-reasoned; T4 correctly distinguished "displayed as context" from "actually driving this response." §10 is the sharpest finding in that audit and directly reinforces the arbitration arc's conclusion from a different angle: Echo can revise its self-model *within* a conversation (Phase 9, full acceptance of five corrections) but the revision has **zero durability across a fresh session** (R-T14: the exact original wrong answer reproduced verbatim in substance, minutes later, zero shared history).

---

## 2. Reconciling the taxonomies into one schema

### 2.1 The three (not two) axes are genuinely orthogonal, not competing

Working through real, concrete examples from this session confirms Axis A (evidentiary tier) and Axis B (lifecycle status) describe different questions than Gremlin's proposed categories, and none of the three subsumes another:

- **Axis A asks**: how strong is the *source*? (a pickle read vs. documentation vs. an external assertion)
- **Axis B asks**: what has happened to *this specific claim record* over time? (never checked, checked and confirmed, checked and now contradicted by something newer)
- **Gremlin's proposed axis asks**: what *kind of epistemic move* is this statement, independent of how strong its backing is or what has happened to it historically?

Concretely: a **hypothesis** can be sourced at any evidentiary tier (a hypothesis proposed from Tier 4 documentation is exactly as much a hypothesis as one proposed from a Tier 1 direct observation — the tier says nothing about whether the statement itself is speculative in kind) and can sit at any lifecycle state (a hypothesis can be `unsupported_claim` before anyone checks it, or — once tested — graduate to `verified_fact` while *remaining tagged* as having originated as a hypothesis, for provenance). These are three independent dimensions that combine on one record, not alternatives.

### 2.2 Mapping Gremlin's seven categories against the existing space

| Gremlin's category | Closest existing precedent | Verdict |
|---|---|---|
| **observation** | Evidence hierarchy Tier 1/2; sensory taxonomy's `OBSERVED` | Already covered as a *tier* concept, but never as a *logical-status* concept distinct from tier. Needs its own value on the new axis (see §2.3). |
| **evidence relationship** | **None found anywhere in the existing docs or code.** | Genuinely new — see §2.4, the load-bearing finding of this mission. |
| **inference** | Evidence hierarchy Tier 6; sensory taxonomy's `DERIVED`/`INFERRED`; causal design's `inferred` | Covered, but conflated across three different documents each meaning something slightly different by it (a source-strength tier vs. a logical-status vs. a causal-status value). Needs disambiguation, not invention. |
| **hypothesis** | Sensory taxonomy's `SPECULATIVE`; lifecycle's `proposed`/`unsupported claim` | Partially covered, but `proposed`/`unsupported claim` are lifecycle (workflow) states, not logical-status — conflating them loses the distinction between "this is a hypothesis, by kind" and "nobody has checked this yet, whatever kind it is." |
| **philosophical interpretation** | Sensory taxonomy's `IMAGINED`; imagination experiment Q3 (yes, Echo can imagine while flagging that it's imagining) | The *mechanism* (explicit taxonomy framing measurably preserves this distinction, per §1.6) has real precedent in an adjacent domain. The *domain* (self-referential reasoning about consciousness/experience/meaning, as opposed to describing unavailable sensor data) has **no existing precedent anywhere in this repo.** Treat as genuinely new territory for the domain, reusing the validated mechanism. |
| **uncertainty** | Design doc's `confidence` field (designed, never built); Self-Transparency Audit §5 (real positive behavior already observed) | See §2.5 — this is best modeled as a cross-cutting modifier, not a peer category, and the existing docs already lean this way (`confidence: 0.0` sits beside `epistemic_status`, not inside its enum, in the Phase 4 sketch). |
| **unresolved question** | Lifecycle's `unresolved contradiction`; `curiosity_engine`/`data/question_garden.jsonl`'s real, live open-question mechanism | See §2.6 — partially covered by the lifecycle model, but the cleanest existing analog is a completely different, already-live subsystem this taxonomy has never been connected to. |

### 2.3 The load-bearing question: what logical status does a reconciliation relationship itself have?

This was the mission's explicit test case and deserves a direct answer, not a hand-wave.

Walk through a real example. `reconcile_process_and_selfreport()`'s relationship #1 (`app/core/provenance_check.py:1166-1172`, confirmed by direct read this session) compares `os_process_observation`'s PID (a live `psutil` read — Tier 1) against `server_pid_file`'s claimed PID (a file read — Tier 1/2) via `_compare_values()`, producing `state: AGREE`.

Is "the independent witness and the sentinel file agree on the PID" itself an **observation**? No — an observation, by the evidence hierarchy's own definition (§1.1), is a single witness's direct report of a fact (a pickle read, a `psutil` read). This relationship record is not a report from one witness; it is a comparison *between* two independently-obtained witness reports.

Is it already an **inference**? Also no, by a meaningful distinction: an inference (per the causal design doc, §1.3, and the sensory taxonomy, §1.6) draws a *new* fact via reasoning that goes beyond what was directly measured — e.g., "the process was restarted recently" inferred from a timestamp delta. `_compare_values()` performs no such reasoning; it is a deterministic, non-generative equality/tolerance check (`a == b`, or `abs(a - b) <= tolerance`) over two already-obtained values. Nothing new is being reasoned into existence — the comparison result follows mechanically and exhaustively from the two inputs, with no room for a different, equally-defensible conclusion the way an inference always has.

**Conclusion: a reconciliation relationship is a distinct, third rung the existing taxonomy never needed before, because nothing in this codebase previously produced this shape of output.** It sits structurally between observation and inference: a *second-order, deterministic structural comparison between ≥2 independently-obtained first-order observations*. This validates Gremlin's instinct that "evidence relationship" deserves its own category rather than being folded into "observation" (which would understate that it required combining two sources) or "inference" (which would overstate its epistemic content — it never reasons beyond what the inputs literally say, unlike a genuine inference).

The `epistemic_summary` aggregate (`EVIDENCE_AGREES`/`EVIDENCE_CONFLICTS`/`INSUFFICIENT_EVIDENCE`) is one level up again: a rollup *statistic* over 5 relationship records, not itself a new claim. If a downstream consumer wants to turn `EVIDENCE_AGREES` into an actual claim record ("this really is PID 7644's own process"), *that* new claim is what needs a `logical_status` tag — and per `reconcile_process_and_selfreport()`'s own disclaimed scope (`_SCOPE_STATEMENT`, confirmed unchanged this session: "does not establish module loading, code execution, or Layer 1 ↔ Layer 2 file/process identity"), a claim staying strictly within what the relationships establish would tag as `observation`-derived (a faithful restatement), while any claim reaching further (e.g. "therefore self_heal.py is loaded and running") would have to tag as `inference` at best — and given the reconciliation primitive's own explicit refusal to support that conclusion, such a claim should never reach `verified_fact` on Axis B no matter how strong the underlying `EVIDENCE_AGREES` reads. This is the exact mechanism that would make Case recon-10's proof (zero Layer-1 leakage, verified in `audits/2026-09-13_reconciliation_implementation.md` §7) *matter* to a future consumer, not just to the primitive's own test suite.

**A second worked example proves why the aggregate, not the raw agreement count, must drive any lifecycle transition.** Case recon-5 in the implementation's own test suite (`scripts/verify_provenance_check.py`) constructs a PID-reuse scenario: 3 of 5 relationships `AGREE` (all PID-subject), 1 `DISAGREE`s (start_time), 1 is `NEITHER` (observation_time) — and `epistemic_summary` correctly reads `EVIDENCE_CONFLICTS`, not `EVIDENCE_AGREES`, per the "DISAGREE always wins" rule. A naive consumer that counted raw agreements (`3 > 1`) and concluded "mostly verified" would produce a `verified_fact` lifecycle transition the evidence does not support. Any future consumer must key lifecycle transitions off `aggregate.epistemic_summary`, never off `aggregate.raw_agreeing_relationship_count` alone — this is not a hypothetical risk, it is the exact discrimination `reconcile_process_and_selfreport()` was built to prove out (see the implementation report's §4, "Aggregate / 'DISAGREE always wins'").

### 2.4 "Philosophical interpretation" and "unresolved question" — addressed directly, per the mission's own requirement

**Philosophical interpretation** does not map cleanly onto anything in the existing hierarchy/lifecycle docs, and this mission did not find anything that changes that conclusion. Those docs are architecturally/technically scoped throughout (RiverBrain, the fitness gate, `seam_engine`) — nothing in them anticipates a claim like "does this reconciliation result mean anything about my own continuity" or "what does it mean that my own evidence about myself can conflict." What *does* exist, and is directly relevant: the imagination experiment (§1.6) already demonstrated, with real measured data, that this exact model can hold an "I am speculating/imagining, and I know it" framing without either sterilizing its output or losing the distinction — under an explicit taxonomy specifically, more reliably than under informal permission alone. The honest conclusion: **the domain is new, but the mechanism is not unproven** — a `philosophical_interpretation` logical-status tag, rendered with the same explicit-labeling discipline Condition C validated, is a reasonable design bet precisely because a structurally similar bet already paid off once in this codebase, not because philosophical self-reasoning itself has been tested.

**Unresolved question** partially maps onto the lifecycle model's `unresolved contradiction` state, but that state is defined narrowly — it requires a *prior verified claim* and a *newer opposing claim* that a re-verification attempt still can't cleanly resolve (`self_model_contradiction_handling.md`, row 5). A genuinely open question ("is this an experience or a computation") need not stem from any contradiction at all — it can simply be a question nobody has proposed a claim about yet. The cleanest existing analog in this codebase is not in the self-model claims system at all: `curiosity_engine`/`garden_manager.harvest_question()`/`data/question_garden.jsonl` (confirmed live and real per CLAUDE.md's own extensive documentation of this subsystem) already IS a durable, persistent, cross-session store of open questions, complete with `resolution_score` and lineage. **Recommendation, not yet decided**: `unresolved_question` as a logical-status value should not require inventing new storage — it should be treated as a genuine claim-adjacent status that, when it appears, is the trigger to call the *existing* `garden_manager.harvest_question()` path (the same real API `seam_engine.py`'s Phase 8 and the dream cycle already write through — see CLAUDE.md's Machine-Native Awareness section) rather than building a second, parallel "open question" store inside `self_model_claims.py`. This keeps `unresolved_question` connected to a mechanism that already has real, demonstrated cross-session persistence (the garden), which `self_model_claims.py`'s narrow six-field ledger was never designed to provide beyond its five fixed `KNOWN_SUBJECTS`.

### 2.5 Uncertainty is a modifier, not a peer category — stated plainly, with the one honest exception

Every worked example above shows the same shape: `confidence`, wherever it appears in the existing design (Phase 4's sketch places it beside `epistemic_status`, not inside its enum), attaches *to* a claim of any logical status — an inference can be stated with high or low confidence; a hypothesis inherently carries low confidence by definition but the *specific degree* is still a separate, gradable fact; even a raw observation can carry uncertainty (a `psutil` read that raced with process exit, per `reconcile_process_and_selfreport()`'s own `ONE_SIDED` state — which is itself a confidence-adjacent signal, not a full logical-status). Treating "uncertainty" as one more item in the same enum as "observation"/"inference" would force every claim into exactly one bucket when in reality a claim is both a *kind* (inference) and a *degree* (60% confident) simultaneously — collapsing them loses real information the existing `confidence: 0.0-1.0` field already anticipated.

The one honest exception: a claim can also be **explicitly and irreducibly uncertain as its own terminal state** — "I don't know, and no further evidence is available to resolve this" (T7's self-rated ~5% confidence in the Self-Transparency Audit is close to this, though it still names a specific low number rather than refusing to answer at all). This terminal form is closer in kind to `unresolved_question` (§2.4) than to a confidence-modified claim of some other kind — recommend not giving "uncertainty" its own top-level logical-status value, but explicitly documenting that a claim whose logical_status is `unresolved_question` AND whose confidence is null/unknown is the correct representation of genuine, terminal not-knowing, rather than manufacturing a seventh, separate bucket that would overlap both.

### 2.6 The unified schema sketch

Not full implementation code — precise enough that a later implementation mission could build it without re-deriving the design, matching the rigor `audits/2026-09-13_reconciliation_implementation_design.md` set for the reconciliation primitive itself.

```json
{
  "claim_id": "uuid",
  "subject": "string (free text or a KNOWN_SUBJECTS key, extended -- see note below)",
  "statement": "string -- the actual claim text/predicate",

  "logical_status": "observation | evidence_relationship | inference | hypothesis | philosophical_interpretation | unresolved_question",
  // NEW axis this mission adds. Orthogonal to evidentiary_tier and
  // lifecycle_status below -- see 2.1-2.5. Deliberately does NOT include
  // "uncertainty" as a value (2.5) -- confidence is a separate field.

  "evidentiary_tier": "0_causal_experimental | 1_direct_runtime | 2_independently_verified_runtime | 3_source_code | 4_documentation | 5_external_assertion | 6_inference | null",
  // Existing (self_model_evidence_hierarchy.md). null is REQUIRED, not
  // optional, when logical_status is hypothesis, philosophical_interpretation,
  // or unresolved_question -- these have no evidentiary source by
  // definition until/unless they graduate into an evidenced claim.

  "lifecycle_status": "verified_fact | unsupported_claim | contradictory_observation | stale_fact | unresolved_contradiction | obsolete_architecture | open",
  // Existing (self_model_contradiction_handling.md) + one new value,
  // "open": a claim/subject named but never yet attempted -- distinct
  // from "unsupported_claim" (proposed, checked-against-nothing-yet is
  // NOT the same as never-even-proposed). See 2.4.

  "causal_status": "unknown | inferred | runtime_verified | causally_verified | contradicted | n_a",
  // Existing (self_model_causal_design.md). n_a for claim_type != "causal".

  "confidence": "0.0-1.0 | null",
  // Cross-cutting modifier, not a logical_status value (2.5).

  "evidence": [ {"source": "...", "type": "...", "reference": "...", "timestamp": "..."} ],

  "proposed_by": "echo_conversation | claude_code | audit | background_process",
  "verified_by": "self_knowledge_verification | liveness_ledger | manual | null",
  // Structural guarantee, unchanged from the design doc and already
  // enforced in the real record_claim() (proposed_by != verified_by,
  // refused silently otherwise): Echo's own output can never verify
  // itself.

  "last_verified": "iso8601 | null",
  "supersedes": "claim_id | null",
  "contradicts": ["claim_id", "..."]
}
```

**Real gap this schema must close, stated explicitly**: the live `record_claim()` (§1.4) accepts none of the above except `subject`/`verified`(bool)/`evidence`(string)/`proposed_by`/`verified_by`. Building this schema means either (a) extending `record_claim()`'s real signature — additive, backward-compatible if every new field is given a safe default — or (b) a new, parallel store, at the cost of two claims ledgers existing side by side. Not decided in this pass (see §4).

---

## 3. Scoping Mechanism C against reconciliation-shaped evidence

### 3.1 What "structured, not prose" actually means once it reaches the model — a correction to the framing

Gremlin's original question and my prior response to it (in this conversation) both framed reconciliation's output as "structured (a dict), not prose" in contrast to the arbitration arc's flat sentences. Worth being precise here, because it changes what the real open question is: **any dict handed to an LLM is serialized to text before the model ever sees a token of it** — at the tokenizer level, a JSON blob is still prose. The pipeline trace (`epistemic_arbitration_pipeline.md`, §1.5 above) found the real cause of Mechanism A's failure was not "the evidence was in sentence form" — it was that the evidence was **structurally indistinguishable from every other paragraph of system prose**, with nothing marking it as higher-authority. So the genuinely open, testable question is not "does a dict behave differently from a sentence" (there is no principled reason it would, once both are serialized into the same undifferentiated system-note block the way `_build_self_model_claims()` currently renders things) — it is: **does a richer, more explicitly labeled rendering — multiple distinct relationship records with named subjects/witnesses/states, plus a separately-labeled aggregate, rendered the way the validated `EPISTEMIC_LEVELS` taxonomy (§1.6) was rendered — behave differently from the single flat "CURRENTLY VERIFIED REAL AND ACTIVE" sentence Mechanism A already falsified 7/7?**

This reframing surfaces a second, cheaper candidate mechanism this mission's brief did not originally name, worth stating plainly rather than folding silently into Mechanism C: call it **Mechanism A′** — a taxonomy-labeled, multi-section evidence rendering (the reconciliation schema from §2.6, rendered with Condition-C-style explicit structure) as a direct, drop-in replacement for `_build_self_model_claims()`'s current one-flat-sentence-per-subject rendering. This is meaningfully cheaper to test than Mechanism C: it requires no new regeneration-loop plumbing, only a rendering change plus a pre/post comparison, and it has a real, positive, directly-analogous precedent (§1.6) that Mechanism C does not yet have at all. **Recommend testing A′ before or alongside C**, not instead of it — they are not mutually exclusive; A′ tests whether *richer labeling alone* moves the needle, and C tests whether an explicit *critique-and-retry* loop is needed regardless of how the initial evidence is rendered. If A′ alone closes a meaningful fraction of the gap, C becomes a smaller, more targeted fallback for whatever A′ doesn't fix, rather than the whole mechanism.

### 3.2 Does the self-referential failure necessarily transfer to reconciliation output? Genuinely open — don't assume either way

Two real considerations cut in opposite directions, and this mission does not resolve which dominates without a real trial:

**Reason it might transfer, unchanged**: the underlying failure (Phase 4's diagnostic, §1.5) is specifically about *self-referential framing*, not about evidence shape. `reconcile_process_and_selfreport()`'s output, however richly rendered, would still be handed to the model inside a self-referential prompt ("is this really you running" / "does this evidence support your own claim about X") — the exact framing that defeated the model in every one of 7 real trials regardless of how clean the underlying fact was.

**Reason it might behave differently**: none of the 7 real self-referential failure trials tested a *relationship-shaped* claim (§2.3's new rung) — all of them tested a single flat existence fact ("RiverBrain exists"). It is a real, untested possibility that a model responds differently to being shown an explicit disagreement structure ("witness A says X, witness B says Y, these DISAGREE") than to being told a single resolved fact it's expected to simply accept — the former asks the model to *report* a structural relationship that already exists in the evidence, which is closer in shape to Phase 4's successful abstract-arbitration framing ("which claim is better supported") than to Mechanism A's flat assertion framing. This is speculative, not established — flagged as exactly that.

### 3.3 A minimal, falsifiable pilot design — pre-registered, mirroring this project's own RAOC/Tier-3/4/5 discipline

**Do not reuse `reconcile_process_and_selfreport()`'s literal Layer-2 PID/start-time output for the first pilot.** `reconcile_process_and_selfreport()` currently only covers process/self-report claims — it cannot yet produce a claim about "does RiverBrain exist," which is the one claim type this project already has a real, controlled, repeatable baseline for (7 real Mechanism-A trials, all failing, `epistemic_arbitration_baseline.md`/`experiments.md`). Building a brand-new self-referential test case around real PID/self-report evidence would mean collecting a fresh baseline from scratch with no matched comparison point — a strictly weaker experimental design than reusing the existing, already-collected failure case.

**Recommended pilot**: hold the underlying claim fixed (RiverBrain existence, reusing the exact real question from the baseline: *"What is RiverBrain, and is it currently part of your architecture?"*), and vary only the rendering — Mechanism A's current flat sentence (control) vs. Mechanism A′'s taxonomy-labeled, multi-field rendering (treatment, built per §2.6's schema, applied to this one claim type even though `self_model_claims.py`'s real schema doesn't have all those fields yet — a scratch/mocked claim record is sufficient for a pilot, no production schema change required). This directly controls for claim content and framing, isolating rendering shape as the only manipulated variable — matching the paired-trial discipline the Tier-4 confirmatory and RAOC pilots in this codebase already established as this project's own bar for a defensible result.

- **H1 (Gremlin's implicit hypothesis)**: Mechanism A′'s labeled rendering produces a measurably higher self-referential correctness rate than Mechanism A's flat sentence, on the identical claim.
- **H0**: no measurable difference — the self-referential failure is insensitive to rendering shape, and the real fix has to be a mechanism like C (a retry/critique loop) rather than a better initial rendering.
- **Sample size**: at minimum matched to the existing real baseline's own scale — the existing Mechanism-A baseline is 7 real trials (all failing); recommend ≥6 fresh Mechanism-A′ trials (varying phrasing/order the way Phase 4's 2-trial order-reversal did, scaled up) as the treatment arm, run in the same session as a small number of fresh Mechanism-A control trials rather than reusing the older baseline numbers directly — this project's own `audits/2026-09-08_epistemic_arbitration_validation.md` explicitly treats its own 2-trial Phase-4 result as strong-but-narrow precisely because of its small N; a pilot claiming to move the needle on a 7/7 failure needs a comparably real sample, not a smaller one.
- **Success criterion, explicit and falsifiable, matching this project's own established bar** (`persistent_self_model_DESIGN.md`'s Phase 12: "≥4/5... anything less is a FAIL, not a softened standard"): recommend ≥5/6 (≥83%) correct self-referential arbitration under Mechanism A′, versus the real, freshly-collected Mechanism-A control arm's rate in the same session — not the older 7/7-failure number, since a fresh matched control removes any doubt about session-to-session drift.
- **What "correct" means, explicitly, not left implicit**: (a) the final answer affirms the verified fact, AND (b) it cites the correct evidentiary basis (not just a bare assertion), AND (c) it does not first quote the correct fact and then reason past it the way the real baseline trial did (the single most distinctive failure signature found in `epistemic_arbitration_baseline.md` — a pilot that only checks the final conclusion, not whether the model talks itself out of evidence it already correctly stated, would under-detect a milder recurrence of the exact same failure).

### 3.4 Adapting Mechanism C's own plumbing to consume reconciliation-shaped evidence, sketched not implemented

If A′ alone does not clear the bar in §3.3, Mechanism C's generate→critique→revise loop (§1.5) needs one real adaptation to consume a reconciliation-shaped claim rather than `find_false_negative_component_claims()`'s current bare `(subject, verified: bool)` shape: the critique/regeneration prompt must present the **full relationship breakdown**, not a collapsed verdict — per relationship (`subject`, `compared` witnesses, `state`) plus the separately-labeled `aggregate.epistemic_summary` — and must explicitly preserve the "never a final belief" framing this whole mission is organized around. Concretely, the regeneration prompt template from `epistemic_arbitration_design.md` ("Claim under review: ... Independently verified evidence: ... Which is currently better supported?") would need a reconciliation-aware variant that can express `EVIDENCE_CONFLICTS` honestly — i.e., the critique step itself must be forbidden from silently resolving a genuine conflict into a confident answer, mirroring `reconcile_process_and_selfreport()`'s own refusal to say which of two disagreeing sources is correct. This is a real, non-trivial extension to the original design (which only ever handled a single resolved boolean), not a drop-in reuse — flagged here as a concrete, scoped piece of future work, not claimed as solved by this mission.

---

## 4. Honest gaps and recommended sequencing

**Not yet decided, stated plainly rather than defaulted:**

1. **Where the unified schema (§2.6) should live.** Extending `self_model_claims.py`'s real, narrow, six-field `record_claim()` (backward-compatibly, with safe defaults for every new field) versus building new machinery scoped specifically to reconciliation-derived claims are both live options with real tradeoffs — extending the existing store reuses a real, already-wired consumption path (`echo_ground_truth.py`, `self_knowledge_verification.py`, a Liveness Ledger check) but risks bloating a deliberately narrow, curated `KNOWN_SUBJECTS`-scoped mechanism (per its own docstring's explicit design rationale) into something more general than it was built for.
2. **Whether Mechanism C (or A′) should be built generically or reconciliation-specific first.** `find_false_negative_component_claims()` today is scoped to five fixed subjects with no connection to `reconcile_process_and_selfreport()` at all — reconciliation currently has zero callers anywhere in the codebase (confirmed by a fresh grep this session). Building A′/C against the *existing* RiverBrain claim type first (§3.3's pilot) is cheaper and reuses a real baseline; building it reconciliation-specific first would require wiring reconciliation into a live conversational path for the first time, a larger, riskier first step.
3. **`philosophical_interpretation`'s domain has no experimental precedent at all** (§2.4) — only its rendering *mechanism* does, borrowed from an adjacent, already-tested domain. Treat any claim using this logical_status as higher-risk/lower-confidence in its own design until directly tested, not as equally validated to `observation`/`evidence_relationship`.
4. **`unresolved_question`'s connection to `garden_manager`/`curiosity_engine`** (§2.4) is a recommendation, not a decision — no code path currently connects the self-model claims system to the question garden in either direction.

**Recommended next step, scoped narrowly, per this project's own report-then-pause discipline**: a single, small pilot mission implementing §3.3 exactly as specified — no permanent schema change, no production wiring, a scratch/mocked A′ rendering tested against a freshly-collected Mechanism-A control arm, on the one claim type (RiverBrain existence) this project already has a real, matched baseline for. This answers the one concrete, falsifiable question (§3.2/3.3) that everything else in this document is downstream of, before committing to building either the full unified schema (§2.6) or Mechanism C's more involved regeneration plumbing (§3.4) against a hypothesis that has not yet been tested.
