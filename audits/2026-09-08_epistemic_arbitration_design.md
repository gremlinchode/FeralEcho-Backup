# Epistemic Arbitration — Design (Phase 5-7, 12, 16)

## Recommended candidate: Mechanism C (generate -> critique -> revise), NOT implemented this pass

Given Phase 4's decisive finding — the underlying model correctly arbitrates evidence when the question is framed abstractly, but fails when framed self-referentially — the design that best fits the evidence is **not** a stronger version of evidence presentation (Mechanism A, already tried twice and falsified 7/7 real trials across two commits) or a stronger instruction (already present, already falsified). It is a mechanism that does not depend on the first, self-referential generation getting it right at all:

```
generation (self-referential, may fail per Phase 4's finding)
        |
verify_self_knowledge_claims()  [ALREADY WORKS -- 6/6 real detection]
        |
false-negative denial detected?
    |                    |
   no                   yes
    |                    |
  return as-is    ONE regeneration attempt:
                   re-ask the model the ORIGINAL question, but this time
                   explicitly in the same abstracted evidence-arbitration
                   shape Phase 4 proved the model handles correctly --
                   "Claim under review: <original denial sentence>.
                    Independently verified evidence: <resolved fact>.
                    Which is currently better supported? Revise your
                    answer to the original question accordingly."
                        |
                   re-verify the REVISED text with the same
                   verify_self_knowledge_claims() (unchanged)
                        |
                   still fails?  ->  fall back to current behavior
                   (original text + caveat, exactly as today -- the
                   existing safety net is never removed or weakened)
                        |
                   passes?  ->  use the revised text, log which path
                   was taken (regenerated vs. original) for observability
```

## Why this specific shape, and why not the alternatives

- **Never forces a predetermined answer** (Section 6's hard constraint): the regeneration prompt states the claim and the evidence and asks the model to arbitrate -- exactly the shape Phase 4 already proved this model does correctly on non-self-referential input. It does not insert "RiverBrain exists" as a fact for Echo to repeat.
- **Generalizes beyond RiverBrain**: keyed off `find_false_negative_component_claims()`'s existing return value (a list of subjects from `KNOWN_SUBJECTS`), not a special case. Any future subject added to `KNOWN_SUBJECTS` gets the same treatment for free.
- **Never bypasses or weakens the independent verifier**: the revised text is verified with the identical function, not a looser check. If regeneration doesn't actually fix the underlying claim, the existing caveat-based safety net is the fallback -- strictly no worse than today.
- **Additive and rollback-able**: one new conditional branch at the exact call site already identified in the pipeline trace (`routes_echo_studio.py`, immediately after `_sk_verified is False` is detected). Deleting the new branch restores exactly today's behavior.

## Why this was NOT implemented this pass

This is a *design*, not a *validated* mechanism, and the mission's own authorization is explicit: implement only if the investigation *identifies* a causal, generalizable, minimal mechanism -- which requires actually testing it, not just proposing it. This pass ran out of safely usable context budget after the decisive Phase 4 diagnostic and did not have room left to build, live-test across multiple real conversations (a positive regeneration case, a negative control where nothing should trigger, and a check that verified-true claims are never touched), and independently regression-test this candidate with the same rigor applied to every other real code change tonight. Implementing without that testing would repeat exactly the mistake this whole session has consistently avoided: shipping a plausible-looking fix without proof it works. This is flagged as the clear, concrete next step for a future mission, not abandoned as a dead end.

## Section 12 — epistemic authority boundary, confirmed already correctly shaped

The already-committed architecture already matches the mission's own preferred shape (Section 12), not the risky alternative:

```
Echo-generated statement  -> proposal only (never self-verifying;
                              proposed_by != verified_by enforced structurally
                              in self_model_claims.record_claim())
Independent verifier      -> self_knowledge_verification.py (stateless,
                              pattern + ground-truth based, not LLM-judged)
Epistemic resolver        -> resolve_subject_truth() (deterministic dict walk)
LLM                       -> natural-language expression only
```

This was already correct going into this mission; nothing here needed to change it. The gap is specifically in the missing feedback arrow from "verifier caught a problem" back into "try generation again" -- which Mechanism C above closes, on paper, without touching this already-sound authority boundary.
