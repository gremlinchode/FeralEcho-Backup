# Self-Model vs. Memory (Phase 9), and Causal Self-Modeling Design (Phase 10)

## Phase 9 — Self-model ≠ memory, stated with real architectural grounding

A memory system answers "what happened." FeralEcho already has one, real and working: `interaction_log.jsonl`, `council_deliberations.jsonl`, `retrieve_relevant_memories()`. It is genuinely useful and genuinely insufficient for this purpose, for a reason grounded in real, already-gathered evidence rather than definition alone: **memory retrieval in this system is similarity-ranked, not truth-ranked.** Tonight's Retrieval Capacity Proof (R2) measured this directly — a lexically-similar-but-wrong memory can outrank the causally-correct one. A self-model, as this investigation defines it, must answer four further questions memory structurally cannot: *what is true about me* (not just "what was said"), *how certain am I* (memory has no confidence field), *why do I believe it* (memory has no evidence/provenance field distinct from "this text exists"), and *what would prove me wrong* (memory has no verification-status field at all).

The design in `persistent_self_model_DESIGN.md` and `self_model_contradiction_handling.md` is explicitly not "give the memory store better retrieval" — it's a structurally separate store (`memory/self_model_claims.jsonl`) with fields memory doesn't have and doesn't need (`epistemic_status`, `verification_status`, `causal_status`, `supersedes`). This is a deliberate, evidenced design choice: extending `retrieve_relevant_memories()` to somehow also carry confidence/verification would inherit its already-measured unreliability (R2) rather than escape it.

## Phase 10 — Causal self-modeling

Tonight's baseline, already measured, not hypothetical: **0% of Echo's causal claims across the whole audit were specific enough to verify.** The external architecture model built independently the same night could only mark most real causal edges as `RUNTIME VERIFIED` (both ends real, correct temporal order) rather than `CAUSALLY VERIFIED` — with exactly one clean exception, the self-edit fitness gate, whose causal role was established by *reading the deciding comparison in source* (`self_edit_manager.py:2179`, `candidate_quality < current_quality`), not by observing correlation.

### The rule the schema enforces

A causal edge record (same schema shape as an ordinary claim, `claim_type: "causal"`, `subject`/`object` naming the two ends) can only reach `causally_verified` through one of two paths, both real and already precedented in this codebase tonight:

1. **Direct source evidence of the deciding operation** — a specific comparison, branch, or write that mechanically connects A to B, cited by file/line, the same standard the Consequence Authority Map used all night (e.g. `model_task_stats[model_name].setdefault(...)` at `echo_model_orchestrator.py:828-844`, read directly, not inferred from the two things merely existing).
2. **A controlled before/after experiment** — change A, hold everything else constant, observe whether B changes, restore A. Not yet run for any Echo-self-model claim (that's `self_model_experiment_plan.md`'s job), but the pattern is directly precedented by tonight's own Architecture A hot-stove experiment (6-vs-6 matched-pair real trials) and the retrieval capacity proof's own paired-query design.

**Existence + temporal ordering + documentation is explicitly insufficient**, and the schema has no field combination that can express it as sufficient — `causal_status` only ever moves off `unknown`/`inferred` when one of the two evidence paths above is cited in the `evidence` array with a matching `type` (`source` or `experiment`), enforced structurally, not just by convention.

### Worked example, using a real claim from tonight

`RiverBrain.learn() writes model_task_stats, which choose_model() later reads` — this is `causally_verified` today, by path 1: both the write (`echo_model_orchestrator.py:828-844`) and the read (`self_edit_manager.py:1822`/`:2050`, `river_deliberation.py:588`) were directly cited by file/line in tonight's Consequence Authority Map, not inferred. Contrast with `the ground-truth injection block causally changes Echo's response` — this remains `unknown`/`inferred` in the current record, explicitly flagged as such in `verified_external_architecture.md`, because the only evidence available is "the block was present and a response was produced," which is exactly the insufficient existence+ordering pattern this design exists to reject. Closing that gap requires path 2 — an experiment withholding the block and comparing outputs — not yet run, deliberately, since it would require a production code change mid-audit (noted as a real, disclosed limitation in tonight's completed audit, not silently left ambiguous).
