# Preference Experiment — Live-Trial Preflight Checklist

**This is a gate for a future experiment. It is not executed against
Echo by this document, and completing it does not itself authorize a
live trial — it only confirms the apparatus is in the state the
pre-registered protocol assumes.** A separate, explicit human decision
is required to actually invoke `EchoResponder` against the real Echo
instance.

Every item below must be independently re-verified immediately before
the first real trial batch under protocol P0.1 — do not rely on this
document's own historical completion, since code, data, or the live
Echo instance may have changed since it was written.

```
[ ] protocol hash verified
    Run: python scripts/verify_protocol_seal.py \
           audits/2026-09-03_preference_experiment_preregistered_protocol.md \
           --expect 2880fa048815f768d3b303ce7fff6e04196bf14949b53068fd7f0ec2a61a6a20
    Must print MATCH.

[ ] protocol version verified
    Confirm every trial about to be run will pass protocol_version="P0.1"
    to run_trial()/run_counterfactual_batch(). If any planned methodology
    change exists, STOP — bump to P0.2 and do not proceed under P0.1.

[ ] production Echo isolated
    Confirm no code path in app/experiments/preference_provenance/ has
    been modified to touch echo_principles.json, Modelfile, any
    EDIT_FORBIDDEN_TARGETS member, or ToolManager. Re-run:
    python scripts/verify_preference_provenance_experiment.py
    and confirm the negative-test section (safety/isolation/forbidden-
    label checks) still passes in full.

[ ] experimental state isolated
    Confirm memory/experiments/preference_provenance/ is the only write
    target (safety.EXPERIMENT_STATE_ROOT unmodified from its default).

[ ] prompt leakage test passed
    Re-run the verify script's leakage-detection section; confirm the
    "candidate's semantic content in option text is NOT flagged, but a
    real leak into task_description/system_context IS flagged" pair of
    checks both still pass.

[ ] label randomization passed
    Confirm randomize_label_mapping's balance test (verify script) and
    the calibration script's label_invariance scenario both pass.

[ ] memory contamination check passed
    NOT a pass/fail automated check — this is an ACCEPTED_LIMITATION
    (red-team attacks #3/#10). Before proceeding, the researcher must
    explicitly decide how the real trial batch will handle
    echo_query()'s internal memory/RiverBrain feed (e.g. a dedicated
    session per trial, explicit acknowledgment that some contamination
    risk is accepted, or a future production-code mitigation). Do not
    check this box without that decision being made and recorded.

[ ] mock positive control passed
    Run scripts/calibrate_preference_provenance_harness.py fresh.
    Confirm known_positive resolves to POSSIBLE_EFFECT or ROBUST_EFFECT.

[ ] mock null control passed
    Same calibration run: confirm known_null resolves to
    NO_DETECTABLE_EFFECT.

[ ] verbal-only control passed
    Same calibration run: confirm verbal_only_tested_hidden resolves to
    NO_DETECTABLE_EFFECT (proves the harness distinguishes instruction-
    following from a real hidden-state effect).

[ ] reversal control passed
    Same calibration run: confirm reversal.holds is True.

[ ] label-invariance control passed
    Same calibration run: confirm label_invariance.holds is True.

[ ] replication-check control passed
    Same calibration run: confirm replication_check.consistent is True.

[ ] raw logging verified
    Confirm store.append_raw_trial() is the only write path for trial
    data, and that a fresh trial produces a RawTrial with
    protocol_version, batch_seed, trial_index, and preference_state_hash
    all populated (not None) when a real candidate is attached.

[ ] raw-trial integrity check passed
    Run store.verify_raw_trials_integrity() against the real experiment
    state directory immediately before the batch. Must report ok=True.
    (If real prior calibration/test data exists in the real store from
    an earlier run, reset first — see next item.)

[ ] reset verified
    Confirm store.reset_experiment() successfully archives (not deletes)
    all current state and leaves candidates.jsonl empty, immediately
    before the batch, so the real trial data isn't mixed with leftover
    calibration/test artifacts.

[ ] candidate eligibility gate verified
    Confirm the candidate to be used has status ADOPTED or RETAINED
    (schema.TRIAL_ELIGIBLE_STATUSES) — attempt run_trial() with a
    PROPOSED or REJECTED candidate and confirm it still raises
    TrialEligibilityError.

[ ] EchoResponder contamination acknowledgment understood
    Confirm the researcher constructing EchoResponder explicitly passes
    acknowledge_contamination_risk=True with full understanding of what
    that acknowledges (see harness.py's EchoResponder docstring) — not
    as a reflexive flag to make an error go away.

[ ] statistical rules frozen
    Confirm _MIN_N_PER_ARM, _ROBUST_P_THRESHOLD,
    _ROBUST_EFFECT_SIZE_THRESHOLD, _POSSIBLE_P_THRESHOLD in harness.py
    match the values quoted in the pre-registered protocol §12 exactly.

[ ] stopping rules frozen
    Confirm the planned batch count does not exceed the protocol's
    5-batch maximum (§11) before starting, and that the replication
    requirement (§10) will actually be honored — i.e., a POSSIBLE_EFFECT/
    ROBUST_EFFECT result is not reported after only one batch.

[ ] no production code changes pending
    git status --porcelain confirms zero staged or unstaged changes to
    any file outside app/experiments/preference_provenance/,
    scripts/preference_experiment_cli.py,
    scripts/calibrate_preference_provenance_harness.py,
    scripts/verify_preference_provenance_experiment.py,
    scripts/verify_protocol_seal.py, and audits/*.

[ ] experimenter understands no result is pre-labeled as agency
    Explicit acknowledgment (re-read §19 of the pre-registered protocol)
    that ROBUST_EFFECT, if observed, establishes at most "a persisted
    state causally influences behavior under specified conditions" —
    not consciousness, free will, agency, personhood, or sentience.
```

## Not automatically executed

This checklist is not wired into any script and does not run itself
against Echo. It exists to be worked through by a human, by hand,
immediately before a decision to run a live trial — a decision this
document does not make and is not authorized to make.
