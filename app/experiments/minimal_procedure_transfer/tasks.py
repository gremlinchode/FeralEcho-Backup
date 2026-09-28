"""
Task family: MERGE OVERLAPPING INTERVALS.

Standalone, self-contained. Imports nothing from app.* or from any other
FeralEcho module -- deliberately, per this experiment's own safety
requirement not to import anything that could trigger a singleton,
background thread, or production write.

Family definition:
  Input:  a list of [start, end] integer pairs (start <= end), in any order,
           possibly overlapping or "touching" (end_i == start_j).
  Output: the minimal list of merged, non-overlapping [start, end] pairs
           that covers exactly the same set of integer points, sorted
           ascending by start. Two intervals that touch (one's end equals
           the other's start) DO merge -- this is the family's one
           deliberate, non-obvious rule, chosen because it is a common,
           real source of off-by-one bugs (< vs <=) rather than an
           arbitrary difficulty knob.

Reference solver is the ground truth used to compute expected outputs at
task-generation time -- it is never shown to the model, and it is a
completely different code path from anything the model or the sandbox
executor does at grading time (grading just checks the model's own
`solve()` output against the pre-computed `expected` field baked into
each task's hidden_tests).
"""
from __future__ import annotations

import hashlib
import json
import random


def reference_merge(intervals: "list[list[int]]") -> "list[list[int]]":
    if not intervals:
        return []
    ordered = sorted((int(a), int(b)) for a, b in intervals)
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def _gen_one_instance(rng: random.Random, n_intervals: int) -> "list[list[int]]":
    """Generates one random, unsorted interval list with a genuine mix of
    disjoint / overlapping / touching pairs -- not adversarially constructed,
    just seeded random generation with parameters chosen so overlaps are
    common (avoids the degenerate case of an instance set dominated by
    trivially-already-disjoint inputs, which would not exercise the merge
    logic at all)."""
    intervals = []
    cursor = rng.randint(0, 5)
    for _ in range(n_intervals):
        start = cursor + rng.randint(-2, 3)  # can overlap or touch the previous one
        start = max(0, start)
        length = rng.randint(1, 6)
        end = start + length
        intervals.append([start, end])
        cursor = end + rng.randint(0, 2)
    rng.shuffle(intervals)
    return intervals


def _make_task(task_id: str, seed: int, n_intervals: int, n_hidden_tests: int) -> dict:
    rng = random.Random(seed)
    hidden_tests = []
    for i in range(n_hidden_tests):
        inp = _gen_one_instance(rng, n_intervals)
        exp = reference_merge(inp)
        hidden_tests.append({"input": inp, "expected": exp})
    # One illustrative example, generated the same way but explicitly
    # NOT one of the hidden_tests -- shown to the model, never graded.
    example_input = _gen_one_instance(rng, max(2, n_intervals - 2))
    example_output = reference_merge(example_input)
    return {
        "task_id": task_id,
        "seed": seed,
        "description": (
            "You are given a list of integer intervals, each written as a "
            "two-element list [start, end] with start <= end. Some intervals "
            "may overlap, and some may exactly touch (one interval's end "
            "equals another interval's start). Merge all overlapping AND "
            "touching intervals into the minimal set of non-overlapping "
            "intervals that covers the same points, and return the result "
            "as a list of [start, end] pairs sorted by start in ascending "
            "order."
        ),
        "example_input": example_input,
        "example_output": example_output,
        "hidden_tests": hidden_tests,
    }


def build_task_set(seeds: "list[int]", prefix: str, n_intervals: int = 5, n_hidden_tests: int = 3) -> "list[dict]":
    return [
        _make_task(f"{prefix}{i:02d}", seed, n_intervals, n_hidden_tests)
        for i, seed in enumerate(seeds)
    ]


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_of(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    # Self-check only -- confirms reference_merge is internally correct
    # against a few hand-worked cases before it is trusted to generate
    # any task's expected output.
    cases = [
        ([[1, 3], [2, 6], [8, 10], [15, 18]], [[1, 6], [8, 10], [15, 18]]),
        ([[1, 3], [3, 5]], [[1, 5]]),   # touching intervals must merge
        ([[1, 2], [4, 5]], [[1, 2], [4, 5]]),  # disjoint, no merge
        ([], []),
        ([[5, 5]], [[5, 5]]),
        ([[1, 10], [2, 3], [4, 5]], [[1, 10]]),  # fully nested
    ]
    for inp, exp in cases:
        got = reference_merge(inp)
        assert got == exp, f"reference_merge({inp}) = {got}, expected {exp}"
    print("reference_merge self-check: OK (6/6 hand-worked cases pass)")
