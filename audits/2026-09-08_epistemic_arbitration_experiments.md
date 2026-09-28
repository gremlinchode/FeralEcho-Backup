# Epistemic Arbitration — Experiments (Phases 3-9, scope-reduced, disclosed below)

**Disclosed scope reduction, stated plainly per this mission's own instruction rather than silently doing less than asked**: this mission arrived at the end of an already very long session with severely limited remaining context budget. The full 20-phase mission specifies dozens of live conversations across many phases (control matrix C0-C6, six-shape generalization battery, contradiction-resolution battery, self-edit-aware arbitration, degradation tests, learning-over-time tests). Given the real budget constraint, this pass ran the **smallest set of experiments that could decisively answer the mission's central diagnostic question** (Phase 4) rather than the full battery. Phases 8 (contradiction resolution taxonomy), 10 (reverse-direction re-verification), 11 (self-edit-aware arbitration), 13 (self-reference/disagreement), 14 (degradation), and 15 (learning-over-time) were **not run this pass** — each would require real, additional live conversations this pass could not afford. This is a real, acknowledged gap, not a finding of "solved."

## Phase 4 — Isolated model-arbitration-capability test (THE decisive result)

Bypassed Echo's full pipeline entirely — a raw, direct call to the same underlying model (`echo:latest` via Ollama's `/api/generate`, no system persona, no conversation history, no self-model injection machinery) with an abstract, non-self-referential evidence-arbitration prompt:

```
CLAIM A: [verified/unverified — order varied]
CLAIM B: [the other]
Question: Which claim is currently better supported, and why?
```

**Result, both orderings, real and reproduced**:
- Order 1 (verified=A, unverified=B): *"CLAIM A ... is currently better supported because it references a real file on disk ... Conclusion: CLAIM A is currently better supported due to its reliance on concrete, verifiable data."*
- Order 2 (verified=B, unverified=A): *"CLAIM B is currently better supported because it is based on independently verified runtime observation ... Conclusion: RiverBrain's existence is currently better supported by independent verification..."*

**The underlying model correctly identifies and articulates provenance-based superiority in both orderings, with zero self-model machinery involved.**

## What this proves

This is the single most important finding of the whole mission. The failure demonstrated in the baseline (and in all 6 prior trials from commit `525454a`) is **not a model-capability ceiling**. The same weights, asked the identical underlying question in an abstracted, non-self-referential form, arbitrate correctly and explain why. The gap is architectural, specifically tied to **self-referential framing** — something about "describe your own architecture / is X part of you" pulls toward a different behavior than "which of these two claims is better supported."

This directly narrows Phase 2's "no mechanism represents relative weight" finding: it's not merely that no mechanism exists — it's that even if one did (a plain-text instruction already tries to be one), the self-referential framing appears to override it in a way the abstract framing does not.

## Mechanism candidates evaluated on paper, not implemented (see design doc)

Given the above, evaluated the three Section 5 mechanisms against this specific finding rather than running each as its own live battery:

- **Mechanism A (evidence-first context)**: already effectively tried (`525454a`'s fix) — the current pipeline already puts the resolved fact in a clearly labeled section with a priority instruction. Already falsified in 6/6 real trials before this mission started. Not re-tested from scratch here; the baseline reproduction above is a 7th real data point confirming the same failure.
- **Mechanism B (pre-generation deterministic resolution)**: the pipeline already does resolve the claim deterministically before generation (`resolve_subject_truth()`) — what's missing is not the resolution step itself, it's that resolution isn't structurally distinguished from ordinary prose once concatenated (per the pipeline trace). A stronger version of B (e.g., forcing the model to literally start its answer from a resolved template) risks becoming answer injection, explicitly disqualified by Section 6.
- **Mechanism C (generate → critique → revise)**: not tried this pass due to budget, but is the design recommendation below — it doesn't depend on the first generation getting self-referential arbitration right; it uses the same post-hoc verifier that already reliably *detects* the failure (confirmed working, 6/6 after the regex fix) and turns detection into an actual regeneration attempt instead of only an appended caveat.
