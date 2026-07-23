#!/usr/bin/env python3
"""
verify_seam_engine.py — discrimination tests for app/core/seam_engine.py's
check_pair(), the same style as scripts/verify_liveness_ledger.py: prove the
evaluator actually discriminates a real contradiction from ordinary noise,
rather than trusting that it "looks right."

Five cases:
  1. Strong stable positive correlation, final reading VIOLATES it        -> seam
  2. Strong stable positive correlation, final reading CONSISTENT with it -> no seam
  3. Strong stable negative correlation, final reading VIOLATES it        -> seam
  4. No real historical relationship at all, wild simultaneous values     -> no seam
  5. Not enough history yet (< minimum)                                  -> no seam
"""
import random
import sys

sys.path.insert(0, ".")
from app.core.seam_engine import check_pair, _MIN_JOINT_OBSERVATIONS


def _linear_series(n, slope=1.0, noise=0.05, seed=0):
    rnd = random.Random(seed)
    a = [rnd.uniform(0, 1) for _ in range(n)]
    b = [slope * x + rnd.uniform(-noise, noise) for x in a]
    return a, b


def case_1_violated_positive():
    n = _MIN_JOINT_OBSERVATIONS + 10
    a, b = _linear_series(n, slope=1.0, noise=0.03, seed=1)
    # Establish a clean positive relationship, then break it on the last point:
    # a spikes up, b crashes down — the opposite of everything before it.
    a[-1] = max(a) + 0.8
    b[-1] = min(b) - 0.8
    return check_pair(a, b) is not None


def case_2_consistent_positive():
    n = _MIN_JOINT_OBSERVATIONS + 10
    a, b = _linear_series(n, slope=1.0, noise=0.03, seed=2)
    # Final point is unusual for BOTH signals individually, but still on the
    # same line as everything else — consistent with the pattern, not a seam.
    a[-1] = max(a) + 0.8
    b[-1] = a[-1] * 1.0  # exactly on the established relationship
    return check_pair(a, b) is None


def case_3_violated_negative():
    n = _MIN_JOINT_OBSERVATIONS + 10
    a, b = _linear_series(n, slope=-1.0, noise=0.03, seed=3)
    # Established: when a goes up, b goes down. Break it: both go up together.
    a[-1] = max(a) + 0.8
    b[-1] = max(b) + 0.8
    return check_pair(a, b) is not None


def case_4_no_relationship():
    n = _MIN_JOINT_OBSERVATIONS + 10
    rnd = random.Random(4)
    a = [rnd.uniform(0, 1) for _ in range(n)]
    b = [rnd.uniform(0, 1) for _ in range(n)]  # independent of a
    a[-1], b[-1] = 5.0, -5.0  # wild simultaneous values, but no pattern to violate
    return check_pair(a, b) is None


def case_5_insufficient_history():
    a, b = _linear_series(_MIN_JOINT_OBSERVATIONS - 5, slope=1.0, noise=0.03, seed=5)
    return check_pair(a, b) is None


def case_6_dynamic_threshold_parameter():
    """2026-07-23 (gap-closure plan Phase C1b): confirms check_pair()'s new
    corr_threshold parameter genuinely changes discrimination, not just a
    no-op default. A moderately-correlated pair (r ~0.25-0.35, deliberately
    below the default 0.4 gate) should NOT fire at the default threshold but
    SHOULD fire once explicitly lowered — same violation shape as case 1,
    just with noisier underlying correlation."""
    n = _MIN_JOINT_OBSERVATIONS + 10
    # noise=2.5, seed=3 empirically gives r~0.35 on the history slice (below
    # the default 0.4 gate, above a lowered 0.15 one) — found by direct
    # search over the real _pearson() output, not guessed.
    a, b = _linear_series(n, slope=1.0, noise=2.5, seed=3)
    a[-1] = max(a) + 0.8
    b[-1] = min(b) - 0.8
    default_fires = check_pair(a, b) is not None
    lowered_fires = check_pair(a, b, corr_threshold=0.15) is not None
    return (not default_fires) and lowered_fires


CASES = [
    ("violated positive correlation -> seam", case_1_violated_positive),
    ("consistent with positive correlation -> no seam", case_2_consistent_positive),
    ("violated negative correlation -> seam", case_3_violated_negative),
    ("no historical relationship -> no seam", case_4_no_relationship),
    ("insufficient history -> no seam", case_5_insufficient_history),
    ("corr_threshold parameter genuinely changes discrimination", case_6_dynamic_threshold_parameter),
]

if __name__ == "__main__":
    passed = 0
    for name, fn in CASES:
        ok = fn()
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        passed += ok
    print(f"\n{passed}/{len(CASES)} discrimination cases passed")
    sys.exit(0 if passed == len(CASES) else 1)
