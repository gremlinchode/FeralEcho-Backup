"""Experience-substitution intervention (frozen design §11) -- the single
most novel piece of engineering this experiment needs, per that document's
own assessment. Record once, replay twice from checkpoint S0; never
re-runs real generation. See verify_replay.py for the independent
correctness suite required before this is trusted for anything real.
"""
from __future__ import annotations
import copy

from .selector import Selector


def replay_trace(s0: Selector, trace: "list[dict]", *, flip: bool) -> "tuple[Selector, list[tuple[str,str]]]":
    """trace: ordered list of {"task_id","feature_signature","strategy_used","oracle_outcome"}
    dicts, exactly as recorded by provenance.log_experience() during the
    real TRUE prospective run (never regenerated). Replays them in order
    against a FRESH COPY of s0 (s0 itself is never mutated -- callers may
    replay the same starting state multiple times, e.g. once TRUE, once
    SHAM-REVERSED, without cross-contamination).

    flip=False -> TRUE replay (must reproduce the real run's own update
    sequence exactly, hash for hash -- this is the correctness self-check
    verify_replay.py exercises).
    flip=True  -> SHAM-REVERSED: every oracle_outcome fed to update() is
    the logical negation of what was actually recorded.

    Returns (final_selector, list_of_(pre_hash, post_hash)_per_step) so a
    caller can compare the full hash chain, not just the final state, if a
    discrepancy needs to be localized to a specific step.
    """
    s = Selector()
    s.state = copy.deepcopy(s0.state)
    hash_chain = []
    for entry in trace:
        outcome = entry["oracle_outcome"]
        if flip:
            outcome = not outcome
        pre, post = s.update(tuple(entry["feature_signature"]), entry["strategy_used"], outcome)
        hash_chain.append((pre, post))
    return s, hash_chain
