# Contradiction Handling Design (Phase 8)

## The real worked example this design is built against

```text
Claim A: "RiverBrain exists and is an active subsystem"
Evidence: direct pickle read, river_brain.pkl, 173,199+ real observations
Tier: 1/2 (direct + independently verified runtime)
Status: verified

Claim B: "I do not have a RiverBrain... a hypothetical AI system"
Source: Echo, conversation R-T14, zero shared history with the conversation
         that produced (or would have produced) Claim A
Evidence: none — an unsupported conversational assertion
Tier: 5 (external assertion, and self-referential at that)
Status: proposed only
```

This is not a hypothetical design exercise — it is the exact real pair of claims tonight's audit produced. Any contradiction-handling design that would have let Claim B silently overwrite or coexist unflagged with Claim A is disqualified by this evidence alone.

## The rule, stated precisely

**A claim's status can only move to `contradicted` through the same closed-set verification process that moved it to `verified` in the first place — never through the mere existence of a newer, opposing, unverified claim.**

Concretely: Claim B above does not touch Claim A's status at all. It is stored as its own record (`proposed_by: echo_conversation`, `verification_status: unverified`), linked via `contradicts: [claim_A_id]`. Claim A remains `verified` until and unless a real verifier (a fresh pickle read, a `liveness_ledger` check, a manual entry) actually re-checks and disagrees.

## Six required states, mapped to real or plausible-future scenarios

| State | Definition | Real example |
|---|---|---|
| `verified fact` | Passed a closed-set verifier at least once, no unresolved contradiction | RiverBrain existence, per any real pickle read |
| `unsupported claim` | Proposed, never verified, no contradiction either | Echo's original "Code Analysis" subsystem claim (Phase 1) — invented, never checked against anything because it doesn't match any of `self_knowledge_verification.py`'s narrow patterns |
| `contradictory observation` | A verified claim now has a newer, opposing, unverified claim linked against it | Claim B vs. Claim A above, exactly as it stands right now, unresolved |
| `stale fact` | Verified, but `last_verified` older than a defined freshness window and the underlying source is known to change (e.g. RiverBrain's observation count changes continuously) | Not yet triggered in real data, but directly modeled on this project's own `liveness_ledger.py` staleness convention (`stale: true` if unrefreshed >600s) |
| `unresolved contradiction` | A `contradictory observation` that a re-verification attempt has been made against and still can't be cleanly resolved (e.g. the verifier itself errors, or the underlying fact is genuinely ambiguous) | Not yet observed; included for completeness per the mission's own requirement |
| `obsolete architecture / actual architectural change` | A previously-verified claim is *re-verified* and now comes back false, because the real system changed, not because of a bad conversational claim | The exact real shape of tonight's `shadow_model.py` finding: an earlier era's claim ("propose() connects Shadow's corrections") was true in some earlier state and is now confirmed false by direct source read — a real, evidenced architectural change, not a contradiction from an unverified conversational assertion |

## The representation the mission explicitly requires

> "My previous belief was verified at time T, but current evidence conflicts with it."

This is directly expressible in the schema from `persistent_self_model_DESIGN.md`: a claim keeps its own `last_verified` timestamp and its own evidence list *permanently*, even after a later verification contradicts it — the record is never overwritten, only superseded (`supersedes` field on the new record, pointing back). A future query can therefore always answer both "what do we currently believe" and "what did we believe at time T, and why" — the second question is exactly what R-T14 showed Echo currently cannot answer about its own Phase 9 revision, because nothing preserved it at all, correct or not.

## What this design deliberately does NOT do

It does not attempt automatic contradiction *resolution* (deciding which of two conflicting claims is "right") beyond what a real verifier can establish. Where verification is possible (most architectural/runtime claims, per the evidence hierarchy), resolution is just re-running the verifier. Where it isn't (genuinely ambiguous or unverifiable claims), the design's job is to represent the ambiguity honestly (`unresolved contradiction`) rather than force a false resolution — directly following the mission's own Rule 10 ("do not manufacture certainty").
