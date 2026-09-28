#!/usr/bin/env python3
"""Independent correctness suite for replay.py, required by the frozen
design (§20/§22 item 5) before the experience-substitution intervention is
trusted for anything real: 'a bug here would silently reconstruct the
wrong counterfactual.' Every case is synthetic; no real model call, no
real task, no dependency on anything outside this package.

Usage: python -B verify_replay.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.persistent_routing.selector import Selector
from app.experiments.persistent_routing.replay import replay_trace

PASS = "PASS"
FAIL = "FAIL"
_checks = []


def check(name, cond):
    _checks.append((name, bool(cond)))
    print(f"[{'OK' if cond else 'FAIL'}] {name}")


def main():
    # Case 1: TRUE replay must reproduce a LIVE update sequence exactly,
    # hash for hash -- the single most important correctness property.
    s0 = Selector()
    trace = [
        {"task_id": "t1", "feature_signature": ["2", "dict"], "strategy_used": "DIRECT", "oracle_outcome": True},
        {"task_id": "t2", "feature_signature": ["2", "dict"], "strategy_used": "STEPWISE", "oracle_outcome": False},
        {"task_id": "t3", "feature_signature": ["1", "string"], "strategy_used": "DIRECT", "oracle_outcome": True},
        {"task_id": "t4", "feature_signature": ["2", "dict"], "strategy_used": "DIRECT", "oracle_outcome": True},
    ]

    live = Selector()
    live.state = {k: {kk: dict(vv) for kk, vv in v.items()} for k, v in s0.state.items()}
    for e in trace:
        live.update(tuple(e["feature_signature"]), e["strategy_used"], e["oracle_outcome"])
    live_hash = live.content_hash()

    replayed, chain = replay_trace(s0, trace, flip=False)
    check("TRUE replay reproduces live-update final state hash exactly", replayed.content_hash() == live_hash)
    check("TRUE replay hash chain has one entry per trace step", len(chain) == len(trace))

    # Case 2: s0 itself must never be mutated by a replay call (needed so
    # the SAME s0 can be replayed TRUE and SHAM-REVERSED independently).
    s0_hash_before = s0.content_hash()
    _ = replay_trace(s0, trace, flip=False)
    _ = replay_trace(s0, trace, flip=True)
    check("s0 is never mutated by replay_trace() (checked after two replays)", s0.content_hash() == s0_hash_before)

    # Case 3: SHAM-REVERSED must produce a genuinely DIFFERENT final state
    # than TRUE, on a trace where the flip actually changes an update's
    # direction (not a vacuous check on an all-same-outcome trace).
    true_replay, _ = replay_trace(s0, trace, flip=False)
    sham_replay, _ = replay_trace(s0, trace, flip=True)
    check("SHAM-REVERSED produces a different final state than TRUE", true_replay.content_hash() != sham_replay.content_hash())

    # Case 4: SHAM-REVERSED's own per-entry outcome is the logical negation
    # of the recorded one -- checked directly against the real update()
    # math, not just "the hashes differ" (which could pass for the wrong
    # reason if update() had an unrelated bug).
    s_manual = Selector()
    s_manual.state = {}
    s_manual.update(("2", "dict"), "DIRECT", False)   # trace[0] flipped: True -> False
    s_manual.update(("2", "dict"), "STEPWISE", True)  # trace[1] flipped: False -> True
    s_manual.update(("1", "string"), "DIRECT", False)  # trace[2] flipped
    s_manual.update(("2", "dict"), "DIRECT", False)    # trace[3] flipped
    check("SHAM-REVERSED matches a manually-flipped update sequence exactly", sham_replay.content_hash() == s_manual.content_hash())

    # Case 5: determinism -- replaying the identical (s0, trace, flip)
    # twice must be byte-identical (no hidden randomness in replay itself).
    r1, _ = replay_trace(s0, trace, flip=False)
    r2, _ = replay_trace(s0, trace, flip=False)
    check("Replay is deterministic (same inputs -> byte-identical output, twice)", r1.content_hash() == r2.content_hash())

    # Case 6: empty trace is a no-op, both for TRUE and SHAM-REVERSED --
    # a real edge case (a lineage with a real but empty prospective phase
    # should not crash, and should return s0 unchanged).
    empty_true, chain_e = replay_trace(s0, [], flip=False)
    empty_sham, _ = replay_trace(s0, [], flip=True)
    check("Empty trace: TRUE replay returns s0 unchanged", empty_true.content_hash() == s0.content_hash())
    check("Empty trace: SHAM-REVERSED replay also returns s0 unchanged (nothing to flip)", empty_sham.content_hash() == s0.content_hash())
    check("Empty trace: hash chain is empty", chain_e == [])

    # Case 7: TypeError enforcement (sanitized-feedback contract) survives
    # replay -- a corrupted trace entry with a non-bool oracle_outcome must
    # fail loudly, not silently coerce.
    bad_trace = [{"task_id": "tx", "feature_signature": ["1", "other"], "strategy_used": "DIRECT", "oracle_outcome": "PASS"}]
    try:
        replay_trace(s0, bad_trace, flip=False)
        check("A non-bool oracle_outcome in the trace raises TypeError", False)
    except TypeError:
        check("A non-bool oracle_outcome in the trace raises TypeError", True)

    print()
    n_fail = sum(1 for _, ok in _checks if not ok)
    print(f"{len(_checks) - n_fail}/{len(_checks)} checks passed.")
    if n_fail:
        sys.exit(1)
    print("verify_replay.py: ALL CHECKS PASSED.")


if __name__ == "__main__":
    main()
