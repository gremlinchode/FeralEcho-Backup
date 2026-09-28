# Persistent Self-Model — Design Proposal (Phases 3, 4, 6, 7, 9)

**Status: design only, per this mission's own Implementation Rule. Nothing described here has been built.**

## Phase 3 — Does any existing structure already qualify as a self-model?

Strict six-part test applied to every real candidate (see full inventory in `persistent_self_model_inventory.md`):

| Candidate | (1) About Echo? | (2) Persists across conversations? | (3) Retrievable by Echo? | (4) Can influence future behavior? | (5) Correctable? | (6) Evaluable against external evidence? | Verdict |
|---|---|---|---|---|---|---|---|
| `self_model.json` | Yes | Yes | Yes (via injection) | Yes | Only by the next 130s rebuild — never by a conversational correction | Yes, indirectly (it's built *from* verifiable sources) | **Closest existing candidate — satisfies 5/6**, but property (5) is the wrong shape: it's correctable only by *background telemetry changing*, never by a claim being disputed or confirmed |
| `liveness_ledger.json` | Yes (about system health) | Yes | Yes (names only, via `_build_capabilities()`) | Yes | Yes (re-evaluated every cycle) | Yes — this is itself an evaluator | Satisfies 4/6 — scoped to *system health claims*, not architectural self-description, and Echo never demonstrated retrieving/using it beyond naming checks |
| `interaction_log.jsonl` | Yes | Yes | Yes (via retrieval, unreliably) | Weakly (Retrieval Capacity Proof, R2) | No (append-only transcript, nothing marks entries disputed/confirmed) | No | Satisfies 2/6 |
| `shadow_model.py`'s output | Yes | Yes (logged) | **No** | **No** | N/A | No | Satisfies 1/6 |

**No existing structure passes the test.** `self_model.json` comes closest and should be the foundation to extend, not replaced — it already has a real writer, real readers, and demonstrated influence on behavior. What it lacks is the one property this whole investigation is about: a place for a *disputed or corrected conversational claim* to land, with provenance and confidence, distinct from its existing background-telemetry aggregates.

## Phase 4 — Minimum viable schema

The mission's proposed JSON sketch is close to right but over-specified in one place and under-specified in another, evaluated directly against real evidence:

**Over-specified**: `causal_status: "unknown|correlated|causally_verified"` collapses a real, evidenced distinction (see the evidence-hierarchy document's "Tier 0" section) — a claim can be `RUNTIME VERIFIED` (A and B both really happened, in order) without being `CAUSALLY VERIFIED` (changing A demonstrably changes B). Recommend widening this field's enum to match the external-architecture-model's own already-proven-useful scheme: `unknown | inferred | runtime_verified | causally_verified | contradicted`.

**Under-specified**: the sketch has no field for *who/what proposed the claim* versus *who/what verified it* — these must be separate fields, not folded into `evidence[].source`, because the whole point of the verification gate (Phase 6 below) is that a proposal and a verification are structurally different events with different authority.

**Recommended schema** (JSON, one record per claim):

```json
{
  "claim_id": "uuid",
  "subject": "RiverBrain",
  "predicate": "exists_and_is_active",
  "object": true,

  "claim_type": "architectural | causal | runtime | capability | limitation",

  "proposed_by": "echo_conversation | claude_code | audit | background_process",
  "proposed_at": "iso8601",
  "proposal_evidence_tier": "1|2|3|4|5|6",

  "epistemic_status": "proposed | verified | contradicted | stale | unknown",
  "confidence": 0.0,

  "evidence": [
    {"source": "river_brain.pkl", "type": "runtime", "timestamp": "...", "reference": "model_task_stats sum, direct pickle read"}
  ],

  "verification_status": "unverified | partially_verified | verified | contradicted",
  "verified_by": "self_knowledge_verification.py | liveness_ledger | manual",
  "last_verified": "iso8601 | null",
  "last_contradicted": "iso8601 | null",

  "causal_status": "unknown | inferred | runtime_verified | causally_verified | contradicted",

  "persistence_status": "durable | session_local | never_persisted",

  "supersedes": "claim_id | null",
  "contradicts": ["claim_id", "..."]
}
```

`persistence_status` is the field this whole investigation exists to add — every claim in the schema must honestly answer "does this actually survive a session boundary," which is exactly the property Phase 2's trace showed nothing in the current architecture provides.

## Phase 6 — Can `self_knowledge_verification.py` serve as the verification gate?

**Partially, and only after a real structural change — it was built for a narrower purpose.** Confirmed by direct source read: `verify_self_knowledge_claims()` (`app/core/self_knowledge_verification.py:262-333`) is a pure, stateless function — it takes response text, returns `(caveat, verified)`, and is called from exactly one site (`routes_echo_studio.py:250`) *after* generation, purely to append a warning to the outgoing HTTP response. It has zero persistence of any kind. It already embodies the right *evaluation logic* (checking a claim against `self_model.json` and a static architecture scan) but has no concept of "write this verdict somewhere a future conversation can read."

The minimum change to repurpose it as the Phase 6 verification gate: give it a second, optional side effect — when `verified is True` or `verified is False` (not `None`, the "nothing checkable" case), write a claim record (using the schema above) to a new persistent store, rather than only returning the caveat text. This is additive to the function's existing contract (same return shape, same call site, same fail-open behavior) — not a rewrite.

## Phase 7 — Propose, not declare

The one non-negotiable design constraint, grounded directly in Phase 9's real failure mode (Echo accepted five corrections with zero pushback despite being told to evaluate). **Echo's own conversational output must never be a valid `verified_by` value.** The schema above enforces this structurally: `proposed_by` can be `echo_conversation`, but `verified_by` can only ever be a name from a fixed, closed set of independent verifiers (`self_knowledge_verification.py`, `liveness_ledger.py`, a future direct-runtime-check function, or a manual/human entry). A claim Echo states about itself — correct or not — enters the store (if at all) at `epistemic_status: "proposed"`, `verification_status: "unverified"`, and stays there until one of the closed-set verifiers actually checks it. This is the mechanical enforcement of the mission's own worked example (Phase 7): Echo saying "RiverBrain doesn't exist" must never overwrite a record already marked `verified` by a real pickle read — it can only ever create a *new, competing, unverified* claim that the contradiction-handling logic (see `self_model_contradiction_handling.md`) then has to reconcile against the existing verified one.

## Final Research Question — two-part answer

### Part 1: What is the minimum architectural change required?

Not a new subsystem. Two additive changes to code that already exists and already does almost the right thing:

1. **A new, small, append-only claims store** (`memory/self_model_claims.jsonl`, following the schema above) — genuinely new, but structurally identical in shape to every other append-only ledger this project already has (`self_edit_attempt_ledger.jsonl`, `dissent_log.jsonl`, `seam_log.jsonl`) — same pattern, new content.
2. **One new side effect on `verify_self_knowledge_claims()`**: when it produces a definitive verdict (`verified is True` or `False`), write a claim record instead of only returning a caveat string. This reuses the exact evaluation logic already proven live tonight (R-T16's real `faiss_atomicity` catch) — it does not require building a new verifier.

Then, symmetrically, **`echo_ground_truth.py` needs one new slice builder** (`_build_self_model_claims()`) that reads the new store and surfaces `verified` claims (never `proposed`-only ones) into future conversations — closing the loop Phase 2 traced as broken. This mirrors the exact pattern the Consequential Learning Loop Design used for self-edit tonight (`_build_targeted_prompt()` reading the attempt ledger) — same shape, applied to Echo's self-model instead of self-edit's code generation.

### Part 2: How would we know we built a self-model rather than another memory system?

Not by inspecting the schema — a JSON file with `confidence` and `evidence` fields is not, by itself, evidence of anything. By running the Phase 12/15 experiment exactly as specified (`self_model_experiment_plan.md`): plant a verified correction, close the session, open a genuinely fresh one, and ask the same question. **A memory system would retrieve the correction inconsistently, the way `retrieve_relevant_memories()` already does today** (competing on lexical similarity against everything else ever said). **A self-model would surface it reliably, every time, because it's injected as a `verified` fact through the ground-truth channel, not fished for through similarity search.** The single decisive test already exists and already has a real, damning baseline result to compare against: R-T14, tonight, where the *current* architecture (no persistent self-model) failed this exact test. Building the two changes above and re-running that identical test, verbatim, is the actual acceptance criterion — not a design review, not a code inspection, a repeat of R-T14 with a different real outcome.
