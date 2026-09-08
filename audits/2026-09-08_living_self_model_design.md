# Living Self-Model — Design (Phase 2-6, 10)

## Core principle preserved
`self_model.json` is never its own authority. The new claims ledger (`memory/self_model_claims.jsonl`) requires `proposed_by != verified_by` as a structural guard in `record_claim()` (`app/core/self_model_claims.py`) — refuses silently, not just by convention, if a caller ever passes matching strings. Echo's own text is never a valid verifier.

## Observation / Claim / Verification / Self-model separation (Phase 3)
- **Observation**: `self_model.json`'s raw fields (`river_brain.total_observations`, etc.) — already exists, already real.
- **Claim**: a specific sentence Echo generates about itself — exists only transiently in a response.
- **Verification**: `self_knowledge_verification.py`'s existing 4 checks plus the new Check 5 (`find_false_negative_component_claims`) — an independent judgment against the observation.
- **Self-model / durable epistemic state**: the new `self_model_claims.jsonl` ledger — did NOT exist before this mission; built.

Flow implemented: `observation (self_model.json) -> claim (Echo's text) -> verification (Check 5, independent) -> claims ledger -> retrieval (echo_ground_truth.py's new slice) -> Echo`. Never the reverse.

## Minimum schema actually built (deliberately smaller than the mission's own sketch)
```json
{"timestamp": "...", "subject": "RiverBrain", "verified": false,
 "evidence": "...", "proposed_by": "echo_response", "verified_by": "self_knowledge_verification"}
```
The mission's own sketch (claim_id/predicate/object/confidence/evidence-list/verification_status enum/causal_status) was evaluated and deliberately NOT built in full — see "What was NOT built" below. The 6-field version is the smallest structure that (a) supports the `proposed_by != verified_by` guard, (b) is retrievable by subject, (c) is append-only/auditable, and (d) was actually testable within this mission's real budget. Confidence/causal_status/contradiction-lifecycle fields are real gaps, documented honestly rather than stubbed with fake precision.

## Evidence hierarchy (Phase 5)
Six tiers from the mission map cleanly onto real sources already confirmed in this codebase:
- Tier 1-2 (direct/independently-verified runtime observation): `self_model.json`'s live fields, read fresh each check.
- Tier 3 (source-code evidence, runtime unconfirmed): `echo_cartographer.py`'s static scan (Check 4's own data source — a real, already-documented limitation, per that check's own comment).
- Tier 4 (documentation): CLAUDE.md — deliberately kept LOW-trust; this project's own night documented 3 real doc-lag incidents.
- Tier 5 (external assertion): where a Phase-9-style conversational correction lives today — exactly why it evaporates.
- Tier 6 (inference): unmodeled here, out of scope.

## Verification gate (Phase 6)
`self_knowledge_verification.py` serves this role directly — it already independently checks claims against ground truth (not Echo's own confidence). Extended, not replaced: Check 5 added for the false-negative-denial case Checks 1-4 structurally cannot catch (they only ever flag a POSITIVE fabrication; none can flag Echo confidently denying something real). This asymmetry — confirmed by direct source read of `find_unsupported_architecture_claims()` — is the single most important design finding of this phase, and is exactly the RiverBrain contradiction's shape.

## Causal claims (Phase 10)
NOT built in this pass. The claims ledger's `subject`/`verified` shape only represents existence-type claims (does X exist / is X real), not `A -> B` causal edges with their own evidence/confidence/verification_status. Building this would require a genuinely new representation and a real controlled-intervention testing harness — correctly out of scope for "smallest mechanism that demonstrates the hypothesis," per the mission's own Implementation Rules. Flagged as a real, larger follow-on, not silently dropped.

## Self-edit-awareness (per the coordinator's added acceptance criterion)
1. **Is the new machinery a self-edit target?** Yes, and it was NOT automatically protected. `app/core/self_model_claims.py` (new) and `app/core/self_knowledge_verification.py` (pre-existing, previously UNPROTECTED — a real gap found and closed this mission) were both added to `EDIT_FORBIDDEN_TARGETS` in `self_edit_manager.py`, with an explanatory comment matching Finding 50's own precedent for `reflection_shard.py`.
2. **Does the observer detect drift in what it depends on?** `find_false_negative_component_claims()` resolves `KNOWN_SUBJECTS`' dotted paths against `self_model.json` with a `.get()` chain that returns `None`/falls through to "not really true" on any missing/renamed field — fails closed, not silently wrong. This was directly tested (see `living_self_model_validation.md`, the `drifted_schema_fails_closed` canary) — a simulated field rename (`total_observations` -> `obs_count`) correctly produces `[]` (no false positive), not a crash or a silent wrong verdict. `KNOWN_SUBJECTS` itself is a small, hardcoded dict — the same *shape* of fixed-domain enumeration as `CATEGORIES`/`TASK_TYPE_MAP`, explicitly acknowledged as a real, live instance of the exact temporal-drift pattern found twice earlier tonight, mitigated (not eliminated) by (a) staying deliberately small/curated rather than trying to be exhaustive, and (b) the new Liveness Ledger check below, which will catch silent degradation over time even though it cannot catch "a fifth core subsystem was never added to the dict at all" (a pure-absence case, same limitation `CATEGORIES` originally had).
3. **New Liveness Ledger check**: `self_model_claims_integrity` (19th new check name added to `_CHECKS`), a functional canary — not a log-presence check — testing the real `find_false_negative_component_claims()` against 4 cases including the drift-specific one. Verified live: `pass: true` against the real function, all 4 cases passing (see validation doc for the actual run output).
4. **Tested, not just reasoned about**: yes — see `living_self_model_validation.md` for the direct function-call results, including the real bug this testing caught and fixed (below).

## A real bug found and fixed during this mission's own construction
The first version of Check 5 reused `_sentence_is_checkable()`'s existing `_HYPOTHETICAL_RE` suppression wholesale — and failed on the exact real motivating case: Echo's actual denial ("more of a hypothetical framing than a literal subsystem") got suppressed as "hypothetical," because that regex was built for POSITIVE fabrication claims, not denials. Caught by direct testing before relying on it, not assumed correct. Fixed with a denial-specific checkability rule (only suppress on genuine first-person uncertainty, not on "hypothetical" language, which in a denial sentence is typically part of the denial's own rhetoric, not a counterfactual setup).

## What was NOT built (Implementation Rules gate respected)
- No architecture fingerprint/hashing (Phase 6 of the parent mission) — the mission's own gate ("do not blindly hash the entire repository... determine the smallest useful fingerprint") was never resolved to a concrete answer within budget; building one without that answer would have been scope creep.
- No automatic architecture-change observer (Phase 5's full scope — component appear/disappear detection, route registration diffing, etc.) — the claims ledger plus Check 5 solves the specific, proven RiverBrain-shaped problem; a general observer is a materially larger system, correctly deferred.
- No contradiction lifecycle (proposed -> verified -> active -> stale -> retired) — only a flat `verified: true/false` per entry exists. A real gap, stated plainly.
- No causal edges (see above).
- No full mission Phase 11 (predictive-variable battery) or Phase 13/14 (false-architecture / integrity-attack) live batteries — see `living_self_model_validation.md` for exactly what real live testing was and wasn't run, and why, under this fork's actual context budget.
