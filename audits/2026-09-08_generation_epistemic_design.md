# Generation-Time Epistemic Revision — Design

## What was built, and why each piece is the smallest thing that addresses its own finding

### Fix 1 (Failure 1): unambiguous evidence rendering, with deduplicated resolution logic

**Gap**: `_build_self_model_claims()` rendered a raw, polarity-losing boolean as a bare "VERIFIED FALSE" label, empirically shown to be misread.

**Fix**: a new shared function, `resolve_subject_truth(subject, self_model) -> bool | None`, added to `app/core/self_model_claims.py` — the module that already owns `KNOWN_SUBJECTS`, so the resolution logic lives next to the data it resolves against. `self_knowledge_verification.py`'s Check 5 (`find_false_negative_component_claims`) now calls this shared function instead of its own inline copy of the same dotted-path walk. `echo_ground_truth.py`'s `_build_self_model_claims()` now calls the same function and states the resolved current fact in plain, unambiguous language, using the ledger entry only as supporting history ("a prior response made an INCORRECT claim about this subject") rather than as the primary assertion.

**Why this is the smallest fix, and why the shared-function extraction matters**: two independent implementations of "resolve this dotted path against self_model.json" is the exact `CATEGORIES`/`TASK_TYPE_MAP` duplication failure shape already found twice this session (`audits/2026-09-07_temporal_authority_graph.md`, `audits/2026-09-07_missing_primitive_determination.md`) — a second copy here would have reopened a class of bug this project spent real effort closing hours earlier. This is a pure refactor plus a rendering change; the actual detection logic in Check 5 is unchanged (verified: identical detection results before and after, direct test included).

### Fix 2 (partial, tested and disclosed as insufficient alone): explicit evidence-priority instruction

**Gap**: even with Fix 1, Echo's generation still overrode the correctly-parsed evidence.

**What was added**: one general, non-subject-specific instruction line appended to `_build_self_model_claims()`'s output: *"When your own prior impression of a subject conflicts with a 'CURRENTLY VERIFIED' line above, the verified line is independently checked against real system state and takes priority over an unverified impression or a past unverified statement you made — including one you may have made earlier in this same conversation."*

**Why this form, not a stronger one**: this is an instruction about *how to arbitrate*, not a predetermined answer — it names no subject and asserts no specific fact, satisfying the mission's Section 10 constraint against "always answer X" rules. It generalizes to any future `KNOWN_SUBJECTS` entry, not just RiverBrain.

**Honest result**: tested, and — per the real 5-trial sample in `generation_epistemic_validation.md` — **not sufficient on its own** to reliably close Failure 2. One trial under this exact configuration produced a third, more concerning failure mode (a fabricated paraphrase of the evidence, not merely an override of correctly-quoted evidence). This is reported plainly, not smoothed over: adding a stronger instruction changed *which way* generation failed in at least one observed case, not whether it failed.

## What was explicitly NOT built, and why

- **No generation-time epistemic gate that blocks/rewrites the raw model output.** The mission's Section 6 sketch (a structured CLAIM/STATUS/EVIDENCE block with an explicit "resolve using the evidence hierarchy" instruction) is, in substance, what Fix 2 already is — a stronger version of the same idea, layered directly into the existing context-assembly path rather than as new middleware. Building a *separate* gating component that intercepts and rewrites `final` before or after `_post_synthesis_verify()` was considered and rejected: it would either (a) hard-code a per-subject correction (explicitly forbidden by Section 10), or (b) require a second LLM call to arbitrate the first LLM's output — a technique this project has already reasoned through and rejected once for a structurally similar problem (`self_knowledge_verification.py`'s own docstring: *"a technique with its own reliability problems this project has no particular reason to trust more than the thing being checked"*). Given Fix 2's own instruction-only approach already failed to reliably close the gap, there is no evidence a heavier version of the same idea (more instruction text, more structure) would succeed either — see the validation document's Outcome classification.
- **No hard-coded RiverBrain special case anywhere.** Every change made is subject-agnostic; `RiverBrain` only ever appears in `KNOWN_SUBJECTS`, the same dict the living-self-model commit already established, in `resolve_subject_truth()`, or in the fix's own explanatory comments.
- **No removal or weakening of the existing post-hoc verifier or claims ledger.** Both are unchanged in their own logic (Check 5's detection results confirmed identical before/after the refactor); only the ledger's *rendering* for a future turn's context changed.
- **No new EDIT_FORBIDDEN_TARGETS entries.** No new production module was created this mission (unlike the living-self-model mission); the two touched files (`self_model_claims.py`, `self_knowledge_verification.py`, `echo_ground_truth.py`) — the first two are already protected from the living-self-model commit; `echo_ground_truth.py` was assessed and left unprotected, consistent with its pre-existing status (it was not flagged as needing protection by the living-self-model mission's own self-edit-awareness pass, and this mission did not find new evidence that it should be — noted as an open question for a future pass, not decided here).

## Outcome classification (Phase 17), stated honestly against the real evidence

The mission is explicit: do not claim D/E/F merely because A/B improved. Based on the full evidence (see `generation_epistemic_validation.md` for the real trial counts):

- **A (retrieval improvement)** — not applicable; retrieval was never broken.
- **B (context conditioning)** — **yes, partially, and this is the real, demonstrated result of this mission.** Fix 1 alone measurably changed what Echo does with the evidence (from misreading it entirely to correctly quoting it), which is a genuine context/content improvement, not an illusion. This is real and worth keeping regardless of what happens with Failure 2.
- **C (instruction following)** — **not reliably demonstrated.** Fix 2's explicit instruction did not produce consistent compliance across trials — see the validation document's real pass/fail breakdown.
- **D (evidence arbitration)** — **not demonstrated.** No trial showed Echo explicitly comparing the verified claim against its own prior belief and reasoning about *why* the verified one should win; the closest observed behavior was either an unreasoned override or a fabricated misquotation, neither of which is arbitration.
- **E (persistent epistemic revision)** — already demonstrated at the *storage* layer by the living-self-model commit (unchanged, still true); **not demonstrated at the generation layer** by this mission — a revision that the model's own generation doesn't honor is not epistemic revision in the sense Section 17 means.
- **F (causal self-modeling)** — out of scope for this mission and not attempted.
