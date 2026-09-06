"""
Retrieval-Augmented Outcome Conditioning (RAOC) — experimental package.

Design-only until explicitly authorized to pilot/run. See
audits/echo_raoc_outcome_conditioning_experiment.md for the full,
pre-registered protocol this package implements. Nothing in this
package makes a real model call on import; running an actual trial
requires explicitly calling harness.run_trial() (or the calibration
script), which is a separate, later-gated step from building this code.
"""
