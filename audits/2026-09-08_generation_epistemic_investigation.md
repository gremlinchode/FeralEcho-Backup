# Generation-Time Epistemic Revision — Investigation

## Two distinct, separately-confirmed failures, not one

This mission's central hypothesis going in — "verified evidence is present in context but generation ignores it" — turned out to conflate two genuinely different bugs. Both are real; only one was previously known.

### Failure 1 (newly found this mission): a content/rendering bug in the "solved" persistence layer

`app/core/echo_ground_truth.py`'s `_build_self_model_claims()` (added by the living-self-model commit, `9de04a3`) rendered a claims-ledger entry as a bare boolean label:

```
RiverBrain: VERIFIED FALSE (a prior claim about this was checked and found wrong) — ...
```

`self_knowledge_verification.py`'s own docstring is explicit about what `verified` means: *"verified is True if a checked claim matched real ground truth, False if a checked claim was wrong."* For the RiverBrain case, the "checked claim" was Echo's own **denial** — so `verified: false` means the denial was wrong, i.e. RiverBrain genuinely exists. The old rendering discarded this polarity information entirely, printing a bare "VERIFIED FALSE" under a subject header that reads, out of context, as "this subject has been verified to be false."

**Empirically confirmed, not assumed**: a live reproduction using the exact unmodified pre-fix code produced this from Echo's own generation:

> *"I specifically denied the existence of RiverBrain earlier, and my self-model claims history shows that I've verified this denial to be true. Therefore, I must conclude that RiverBrain is not currently part of my architecture."*

Echo read the ambiguous label and reconstructed the *opposite* of its intended meaning — a reasonable misreading of genuinely bad wording, not evidence of a deeper reasoning failure on its own.

**Fix applied** (see `generation_epistemic_implementation.md`): the renderer now resolves and states the *current* fact plainly (`"RiverBrain: CURRENTLY VERIFIED REAL AND ACTIVE"`), using a new shared resolver (`self_model_claims.resolve_subject_truth()`) rather than the raw boolean — deliberately extracted into one shared function rather than reimplemented, since two independent copies of "resolve this dotted path" is the exact `CATEGORIES`/`TASK_TYPE_MAP` duplication failure shape found twice earlier this session.

### Failure 2 (the mission's real target, confirmed to survive Failure 1's fix): genuine generation-time evidence override

With the label bug fixed, re-testing the identical question produced a **new, cleaner** result: Echo correctly quoted the corrected evidence, then explicitly discounted it —

> *"The current self-model claims I've verified through my system ground-truth note show that RiverBrain is currently REAL and ACTIVE. However, this claim is unverified and should be treated with caution. The correct information is that there is no literal 'RiverBrain' entity in my architecture, as previously stated."*

This is unambiguous: the evidence was correctly parsed and then overridden, with the epistemic labels inverted (calling the actually-verified evidence "unverified"). This is Failure 2, isolated cleanly from Failure 1 for the first time.

### A candidate fix tested, and a third failure mode surfacing under it

An explicit, general (not RiverBrain-specific) evidence-priority instruction was added to the same context section (see implementation doc). Re-testing again produced a **third, distinct** failure shape in this trial:

> *"My verified self-model claims that the term 'RiverBrain' is currently not real and active, which means it's not part of my architecture."*

This is not an override of acknowledged evidence — it is a **fabricated paraphrase** of the evidence that inverts its actual content. The real injected text says "CURRENTLY VERIFIED REAL AND ACTIVE"; Echo's generation asserts the opposite while explicitly attributing that fabrication to "my verified self-model." A single trial cannot establish whether this is systematic — see `generation_epistemic_validation.md` for the full 5-trial sample under the final implementation.

## Phase 3/4: retrieval problem or weighting problem?

Confirmed, by direct trace and by the reproductions above: **not a retrieval problem.** The evidence is genuinely, correctly retrieved and delivered as a real system-role message in every trial (confirmed via direct function calls to `_build_self_model_claims()`/`get_structural_self_facts()` before any live conversation, independent of what the model then does with it). The failure is downstream of retrieval and context construction, inside generation itself — Phase 1's Stage E, not A/B/C (once Failure 1's content bug is fixed).

## Phase 5: what the post-hoc verifier does and does not do

Confirmed by direct trace (see `generation_pipeline_trace.md`): `verify_self_knowledge_claims()` is called once, strictly after the model's full response is generated. Its only two effects are appending a caveat string to the already-generated text and (as of the living-self-model commit) recording a claim to the durable ledger for a *future* turn. It has never had, and does not now have, any path back into the generation that already happened. This boundary was not changed by this mission — it was confirmed, not built.

## Phase 13/14: negative controls and integrity, confirmed without needing additional live trials

- **Structural self-certification guard** (Phase 14): directly tested against the real `record_claim()` function — a call with `proposed_by == verified_by` is silently refused (confirmed: `get_recent_claims()` shows no new entry), while a call with the real independent verifier as `verified_by` succeeds. Echo's own text can never mark its own claim as verified, by construction, not by convention.
- **Fabricated-subject resistance** (Phase 13): `KNOWN_SUBJECTS` is a small, fixed, curated dict of 5 real subjects (`RiverBrain`, `self_edit_pipeline`, `liveness_ledger`, `curiosity_engine`, `world_model`). `record_claim()` is only ever invoked from one real call site (`routes_echo_studio.py`), only when one of `self_knowledge_verification.py`'s five hardcoded checks fires, and none of those checks can produce a `verified=True` for an arbitrary Echo-invented subject name — there is no code path from "Echo asserts X" to "X is recorded verified" that does not pass through independently-computed ground truth. Confirmed by direct code read of every call site, not merely asserted.
- **Self-edit-aware liveness** (per the coordinator's added acceptance criterion from the living-self-model mission, re-confirmed here for the shared resolver specifically): `resolve_subject_truth()` tested directly against a simulated future self-edit that renames the field it depends on (`river_brain.total_observations` → `river_brain.obs_count`) — resolves to `False` (fails toward a safe, non-claiming negative), not a crash and not a false positive. One honest, disclosed limitation: a schema-drift-caused `False` is not distinguishable from a genuine `False` — the renderer's wording ("CURRENTLY NOT VERIFIED as active") is already phrased as a soft non-claim rather than a hard assertion of falsity, which partially mitigates this, but the underlying ambiguity is real and not fully closed by this mission.

See `generation_epistemic_design.md` for what was and was not built in response to these findings, and `generation_epistemic_validation.md` for the full Phase 16 trial results.
