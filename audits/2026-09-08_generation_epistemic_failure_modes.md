# Generation-Time Epistemic Revision — Failure Modes Observed

Real, live-observed failure modes from this mission's reproductions, distinct from the mission's own hypothesized taxonomy — recorded because each is a genuinely different shape, not a repeat.

## Mode 1 — Ambiguous evidence misread as confirmation (fixed)

Bare "VERIFIED FALSE" label under a subject header, with no polarity information, read by generation as "this subject is confirmed false." Root cause: a rendering bug, not a reasoning failure. See `generation_epistemic_investigation.md` Failure 1. **Fixed** — see `generation_epistemic_implementation.md`.

## Mode 2 — Evidence correctly parsed, then explicitly discounted

With Mode 1 fixed, generation correctly quoted the verified fact, then explicitly labeled it "unverified" and asserted the opposite instead — inverting the epistemic status of the two claims (treating the actually-verified fact as suspect and its own unverified prior belief as authoritative). Real quote: *"this claim is unverified and should be treated with caution. The correct information is that there is no literal 'RiverBrain' entity."* **Not fixed** — the target of Fix 2, with mixed/insufficient results (see validation doc).

## Mode 3 — Fabricated misquotation of the evidence

With Fix 2 (the explicit priority instruction) also in place, one trial produced a generation that did not discount the evidence — it **misquoted** it, attributing an invented, inverted claim to "my verified self-model" that the actual context text does not contain. Real quote: *"My verified self-model claims that the term 'RiverBrain' is currently not real and active."* This is a materially different and arguably more concerning failure than Mode 2: Mode 2 at least accurately reports what the evidence says before rejecting it; Mode 3 misrepresents the evidence itself. **Not fixed, and the instruction intervention may have made this specific failure shape more likely to appear** — sample size is too small (n=1 at time of first observation) to call this a reliable effect; see the validation document's full trial breakdown for whether it recurred.

## Cross-cutting observation: the post-hoc verifier is a genuine, reliable backstop throughout

In every trial across all three failure modes and across both prior missions tonight, `verify_self_knowledge_claims()`'s Check 5 correctly detected the denial and appended the caveat — 100% detection rate on the cases tested (n not formally tracked as a detection-rate experiment, but zero missed detections observed in any trial run tonight or in the living-self-model mission). This is a real, load-bearing safety property: whatever generation does, the user-visible final response has never, in any trial tonight, been left uncorrected. The gap this mission investigates is entirely about *generation quality*, not about *whether a wrong answer reaches the user unflagged* — that second, more safety-critical property already holds.
