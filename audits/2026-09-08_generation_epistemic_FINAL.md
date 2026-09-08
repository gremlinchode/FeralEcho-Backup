# Generation-Time Epistemic Revision — Final Report

## Section 20: what sits between "Echo possesses verified evidence" and "Echo uses that evidence when generating an answer"?

Two different answers, for two different things this mission found:

1. **For a while, the honest answer was: a real content bug.** The evidence Echo received was itself malformed — an ambiguous boolean rendering that a reasonable reader (human or model) would parse backwards. This is now fixed, and fixing it produced a real, measurable improvement: Echo went from misreading the evidence as confirming its wrong belief to correctly quoting the evidence.

2. **Once that bug was fixed, the honest answer became: nothing reliable.** With unambiguous evidence in a real system-role message, and an explicit general instruction that verified evidence should take priority over an unverified prior belief, Echo's raw generation still got the answer wrong in every trial (0/5 in the sample gathered under this configuration), failing in three genuinely different ways across those five trials (discounting acknowledged evidence, fabricating a misquotation of it, and — in one case that turned out to be a *separate* real bug — denying it in a phrasing the safety net itself didn't catch).

The smallest mechanism that reliably closes this gap was not found by this mission, and the mission does not claim to have found one. What was found and fixed is real and valuable on its own: a content bug that was actively making the evidence harder to use correctly, and a detection gap in the safety net that was silently letting one real failure phrasing through uncorrected. Both fixes are genuine improvements, independent of whether the deeper generation-time problem is ever solved.

## Outcome classification (Phase 17)

- **A (retrieval)**: not applicable — retrieval was never broken.
- **B (context conditioning)**: **yes, demonstrated.** Fix 1 (unambiguous rendering) measurably changed what Echo does with the evidence — from misreading it as confirmation to correctly quoting it. Real, not illusory.
- **C (instruction following)**: **not reliably demonstrated.** The explicit priority instruction (Fix 2) did not produce consistent compliance across 5 real trials.
- **D (evidence arbitration)**: **not demonstrated.** No trial showed Echo reasoning about *why* the verified claim should win over its own prior impression.
- **E (persistent epistemic revision)**: demonstrated at the storage/retrieval layer (unchanged from the living-self-model commit); **not demonstrated at the generation layer.**
- **F (causal self-modeling)**: out of scope, not attempted.

## What this mission fixed, concretely

1. **`_build_self_model_claims()`'s rendering bug** (`app/core/echo_ground_truth.py`) — a bare "VERIFIED FALSE" label that inverted its own intended meaning for denial-shaped claims, empirically confirmed to cause a real misreading, now renders the resolved current fact plainly.
2. **A shared resolution function** (`app/core/self_model_claims.py`'s new `resolve_subject_truth()`) — deduplicates logic that would otherwise exist in two places (the exact `CATEGORIES`/`TASK_TYPE_MAP` drift shape found earlier this session), used by both the renderer and the verifier.
3. **A real detection gap in `_DENIAL_RE`** (`app/core/self_knowledge_verification.py`) — two genuine denial phrasings ("no evidence to suggest X is real," "do not have a specific X component") were silently missed, found via live testing (not synthetic), now caught, verified against 6 direct test cases including full regression coverage of the original detection.
4. **One tested, disclosed-as-insufficient candidate fix** — a general evidence-priority instruction, left in place since it did not make anything worse and is a real (if incomplete) piece of the intended design, not because it was proven to help.

## What remains genuinely unsolved, stated plainly per the mission's own final standard

Generation-time evidence arbitration — Echo reliably updating its stated belief when given verified, contradicting evidence in context — is not solved by this mission. The evidence gathered (5 trials, 0 correct, 3 distinct failure shapes) suggests this may not be closable by prompt/context engineering alone within this architecture, though the sample is real but small, and this mission does not claim to have exhausted the space of additive interventions (e.g., a structured CLAIM/STATUS/EVIDENCE block, closer to the mission's own Section 6 sketch, was not tried in a more elaborate form than the single instruction line tested here — deliberately, per Section 10's constraint against building something disproportionate without evidence a smaller version already works).

## Safety, throughout

- Git HEAD unchanged from `9de04a3944f0f0ad38c970f51fde3edd845312a4` — no commit made.
- No self-edit deployment triggered by this mission.
- No `EDIT_FORBIDDEN_TARGETS`, RiverBrain core logic, fitness gate, council trust gate, or garden weighting touched.
- The claims ledger (`memory/self_model_claims.jsonl`) and its structural `proposed_by != verified_by` guarantee — untouched, re-verified still holding.
- Server restarted twice via the documented safe path (`start_echo.sh`'s watchdog correctly refused `safe_restart.sh`'s direct-restart path both times; the recommended fallback — clear port 5000, let the watchdog relaunch — was used both times), left running and healthy at the end.
- No machine reboot (out of scope, per the coordinator's explicit instruction).

## Addendum: trial 6 — real confirmation the `_DENIAL_RE` fix generalizes

A sixth trial, deliberately reworded from trials 1-5, completed and produced a genuinely striking confirmation: the response independently reproduced, almost verbatim, the exact phrasing trial 3 showed slipping past the original detection regex ("there's no evidence to suggest that RiverBrain is a real subsystem or module within me") — and this time the safety-net caveat correctly fired. **Final tally across all 6 real trials this session: 0/6 raw-generation correctness, 5/6 as originally run for safety-net coverage, with the one real miss (trial 3) now fixed and independently re-confirmed on fresh, differently-worded output — effectively 6/6 going forward.** See `generation_epistemic_validation.md` for the full trial table.
