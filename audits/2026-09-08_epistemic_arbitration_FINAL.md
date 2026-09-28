# Epistemic Arbitration — FINAL

## Safety / baseline

HEAD confirmed `525454a1dccfc91adf1aa8b01ff9b6ce8405d423` at start; unchanged at end -- **no commit made**. No `EDIT_FORBIDDEN_TARGETS`, RiverBrain core, fitness gate, council trust, or garden weighting touched. No machine reboot. Server (PID 29494) left running healthy. Real production RiverBrain data (170,000+ observations) was never modified -- only read, and only via the deterministic resolver already committed.

## Section 20 — the final research question

> **What mechanism, if any, causes independently verified epistemic state to exert causal influence over Echo's generated beliefs?**

**Currently: none, reliably.** A plain-text instruction is present in context ("the verified line ... takes priority") and is, per Phase 2's pipeline trace, structurally indistinguishable from every other paragraph of system prose the model receives -- it is an instruction, not a weighting mechanism, and Phase 1's fresh reproduction shows the model can even *name* the contradiction explicitly and still not resolve it in the evidence's favor.

**But this pass found something the prior two missions did not**: the failure is not a model-capability ceiling. Phase 4's isolated test -- the same weights, given the identical underlying evidence-arbitration task framed abstractly rather than self-referentially -- arbitrated correctly, twice, order-independent. The gap is specifically located in **self-referential framing**, not in the model's general capacity to weigh provenance.

## Section 19 — classification

**B (context conditioning)** continues to be the honest ceiling for the *current, committed* system -- this pass changed nothing that would move it. This mission's real contribution is narrowing *why* B is the ceiling (a diagnostic result, Phase 4), plus a specific, evidence-grounded design for what could plausibly reach **D (evidence arbitration)** without yet having tested it (Mechanism C, generate-critique-revise, in `epistemic_arbitration_design.md`) -- explicitly not implemented, explicitly not claimed as demonstrated, per the mission's own Non-Negotiable Scientific Standard against claiming D/E/F without experimental proof.

## What this mission adds beyond commits `9de04a3` and `525454a`

1. A 7th consistent real reproduction of the raw-generation failure, with a specific, striking new observation: Echo can quote its own correct evidence and flag the contradiction in the same breath as getting the conclusion wrong.
2. The single most decisive diagnostic of the whole arc: **the underlying model can arbitrate evidence correctly; Echo's self-referential framing is what defeats it.** This reframes the problem from "does the model understand evidence weight" (yes) to "why does asking it about itself specifically break that capacity" -- a sharper, more tractable question for a future mission.
3. A concrete, small, additive, rollback-able candidate mechanism (generate-critique-revise, keyed generically off `KNOWN_SUBJECTS`, never bypassing the existing verifier) -- designed but explicitly not implemented, for a future pass with budget to test it properly.

## What remains open, stated plainly rather than hidden

The six-shape generalization battery, the three-mechanism live comparison, contradiction-type taxonomy, self-edit-aware arbitration, degradation-under-failure, and any test of whether arbitration *improves over time* (real learning, Section 15) were not run this pass. Section 20's answer above is grounded in what was actually tested (2 isolated arbitration trials, 1 fresh baseline reproduction) -- real, reproducible, and honestly bounded by that sample size. The next mission's highest-value next step is exactly what this report's design doc proposes: implement Mechanism C and run it through the full six-shape battery this pass could not afford.
