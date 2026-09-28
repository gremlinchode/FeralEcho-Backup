"""Pre-declared Q2 task dimensions -- frozen protocol Section 2, fixed here BEFORE any
outcome is examined (this file is written before Phase 0 or Stage 1 have made a single
real call). These are the ONLY dimensions any Q2 analysis may test against; none may be
added or changed after seeing data.

Corrected per the adversarial review
(audits/2026-09-27_strategy_characterization_protocol_adversarial_review.md,
audits/2026-09-27_strategy_characterization_protocol_design.md Section 2's correction):
`operation` (exactly 1 task per level among the 6 T-templates) and `arg_count` (5-vs-1)
are structurally confounded with individual-task identity, not merely underpowered, and
are marked ELIGIBLE=False below -- they are retained here for the record (so the
original 4-dimension declaration is not silently erased) but must never be used to
support a Q2 conditional-effect claim. `return_type` is the sole eligible dimension.
`output_cardinality` is retained as a secondary, heavily-caveated check only."""
from __future__ import annotations

# task_id -> {dimension: value}, hardcoded from tasks_v2.py's KT["K2"] registry
# (T1 pick_winner, T2 rank_all, T3 pick_loser, T4 top_two, T5 winner_with_score,
# T6 is_winner), read directly, not re-derived from feature_signature() (which the
# postmortem showed collapses these via shared boilerplate).
TASK_DIMENSIONS = {
    "K2.T1": {"return_type": "str", "arg_count": 1, "operation": "select_best", "output_cardinality": "scalar"},
    "K2.T2": {"return_type": "list", "arg_count": 1, "operation": "full_order", "output_cardinality": "full_collection"},
    "K2.T3": {"return_type": "str", "arg_count": 1, "operation": "select_worst", "output_cardinality": "scalar"},
    "K2.T4": {"return_type": "list", "arg_count": 1, "operation": "partial_order", "output_cardinality": "bounded_collection"},
    "K2.T5": {"return_type": "tuple", "arg_count": 1, "operation": "select_extract", "output_cardinality": "scalar"},
    "K2.T6": {"return_type": "bool", "arg_count": 2, "operation": "membership_check", "output_cardinality": "scalar"},
}

# Confirmation-set (S-split) dimension tags, for Stage 2 only (not used by Stage 1) --
# recorded here for completeness/consistency, not exercised until a Stage 2 is
# separately authorized. S1 pick_winner_dicts (str), S2 winners_by_round (list),
# S3 winner_from_text (str), S4 rankings_by_round (list-of-lists, tagged "list").
CONFIRMATION_TASK_DIMENSIONS = {
    "K2.S1": {"return_type": "str"},
    "K2.S2": {"return_type": "list"},
    "K2.S3": {"return_type": "str"},
    "K2.S4": {"return_type": "list"},
}

# Eligibility, per the adversarial review's correction -- False means "declared, but
# structurally unable to support a Q2 claim; report exploratory numbers if ever computed,
# but never as a finding."
DIMENSION_ELIGIBLE = {
    "return_type": True,          # 2-vs-2-vs-1-vs-1 -- thin, but the only real replication that exists
    "arg_count": False,            # 5-vs-1 -- entire level 2 is a single task (T6)
    "operation": False,            # 1-vs-1-vs-1-vs-1-vs-1-vs-1 -- every level is a single task
    "output_cardinality": False,   # 4-vs-1-vs-1 -- same near-total-confound shape, secondary/caveated only
}
