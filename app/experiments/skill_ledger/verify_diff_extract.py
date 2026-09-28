#!/usr/bin/env python3
"""Independent correctness suite for diff_extract.py, required before trusting it
against real data -- same discipline as verify_replay.py/verify_seam_engine.py.
Every case here is either synthetic or the exact real historical pair already on
disk from strategy_characterization's Stage 1 (re-read, not re-generated)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.skill_ledger import diff_extract as DE

_checks = []


def check(name, cond):
    _checks.append((name, bool(cond)))
    print(f"[{'OK' if cond else 'FAIL'}] {name}")


def main():
    # Case 1: the exact real historical pair (EP-A, K2.T5, STEPWISE, world=1) --
    # failing (rep 2/3) vs passing (rep 0). Both share the identical world (same
    # tag_priority dict literal), differing ONLY in a negation on the tag_priority
    # lookup inside the sort key tuple.
    failing_real = (
        "def winner_with_score(entries):\n"
        "    tag_priority = {'medaj': 1, 'jirow': 2, 'rojav': 3, 'pazeg': 4}\n"
        "    sorted_entries = sorted(entries, key=lambda x: (-x[1], -tag_priority[x[2]], x[0]))\n"
        "    return sorted_entries[0][0], sorted_entries[0][1]"
    )
    passing_real = (
        "def winner_with_score(entries):\n"
        "    tag_priority = {'medaj': 1, 'jirow': 2, 'rojav': 3, 'pazeg': 4}\n"
        "    sorted_entries = sorted(entries, key=lambda x: (-x[1], tag_priority[x[2]], x[0]))\n"
        "    return sorted_entries[0][0], sorted_entries[0][1]"
    )
    pattern = DE.extract_transformation(failing_real, passing_real, "winner_with_score")
    check("real pair: a transformation is extracted (not None)", pattern is not None)
    if pattern:
        check("real pair: precondition is a UnaryOp (the negation)", pattern["node_type"] == "UnaryOp")
        check("real pair: precondition != transformation", pattern["precondition"] != pattern["transformation"])
        check("POSITIVE CONTEXT: enclosing_call is correctly recorded as 'sorted'",
              pattern.get("enclosing_call") == "sorted")

    # Case 2: apply the extracted pattern to the SAME failing code -- must correct it.
    if pattern:
        fixed = DE.apply_skill(failing_real, "winner_with_score", pattern)
        check("apply to source failing instance: produces output", fixed is not None)
        if fixed:
            check("applying removes the negation on tag_priority[x[2]]",
                  "-tag_priority[x[2]]" not in fixed.replace(" ", "") and "tag_priority[x[2]]" in fixed.replace(" ", ""))

    # Case 3: HELD-OUT TRANSFER -- apply the pattern (extracted from world 1) to a
    # FRESH, DIFFERENT world's failing candidate with a completely different
    # tag_priority literal. This is the actual generalization claim -- must still work
    # since this specific bug's diverging subtree never referenced a tag literal.
    failing_fresh_world = (
        "def winner_with_score(entries):\n"
        "    tag_priority = {'nizog': 3, 'renem': 2, 'dulup': 1, 'dogiz': 0}\n"
        "    sorted_entries = sorted(entries, key=lambda x: (-x[1], -tag_priority[x[2]], x[0]))\n"
        "    return sorted_entries[0][0], sorted_entries[0][1]"
    )
    if pattern:
        fixed_fresh = DE.apply_skill(failing_fresh_world, "winner_with_score", pattern)
        check("HELD-OUT: pattern applies to a fresh world's failing candidate", fixed_fresh is not None)
        if fixed_fresh:
            check("HELD-OUT: fresh world's own literal ('nizog' etc.) is preserved, not overwritten",
                  "nizog" in fixed_fresh and "renem" in fixed_fresh)
            check("HELD-OUT: negation removed in the fresh-world candidate too",
                  "-tag_priority[x[2]]" not in fixed_fresh.replace(" ", ""))

    # Case 3b: NEGATIVE CONTEXT -- this is the exact real historical defect found in
    # the first live MVK run (2026-09-27). A max()-based candidate that superficially
    # matches the sorted()-derived precondition's LOCAL shape must NOT be patched by
    # it, because the correct negation polarity is genuinely opposite under max()
    # (confirmed by direct arithmetic during Phase 2 re-derivation, not assumed).
    if pattern:
        max_based_failing_real = (
            "def winner_with_score(entries):\n"
            "    tag_priority = {'zezen': 1, 'jovow': 2, 'josog': 3, 'rotil': 4}\n"
            "    return max(entries, key=lambda x: (x[1], -tag_priority[x[2]], x[0]))"
        )
        result = DE.apply_skill(max_based_failing_real, "winner_with_score", pattern)
        check("NEGATIVE CONTEXT: sorted()-derived skill correctly refuses to apply "
              "inside a max() call (honest non-application, not a wrong patch)",
              result is None)

    # Case 3c: EXISTING GENERICITY, re-confirmed with the context gate active -- the
    # already-proven cross-world sorted()-to-sorted() transfer must still work.
    if pattern:
        sorted_based_fresh_world = (
            "def winner_with_score(entries):\n"
            "    tag_priority = {'nizog': 3, 'renem': 2, 'dulup': 1, 'dogiz': 0}\n"
            "    sorted_entries = sorted(entries, key=lambda x: (-x[1], -tag_priority[x[2]], x[0]))\n"
            "    return sorted_entries[0][0], sorted_entries[0][1]"
        )
        fixed3 = DE.apply_skill(sorted_based_fresh_world, "winner_with_score", pattern)
        check("EXISTING GENERICITY (with context gate active): still transfers "
              "correctly to a fresh sorted()-based world", fixed3 is not None
              and "-tag_priority[x[2]]" not in fixed3.replace(" ", "")
              and "nizog" in fixed3)

    # Case 3d: SERIALIZATION -- the enriched precondition (including enclosing_call)
    # must survive a real ledger write/reload round-trip.
    if pattern:
        import tempfile, os as _os
        from app.experiments.skill_ledger.ledger import Skill
        with tempfile.TemporaryDirectory() as td:
            import app.experiments.skill_ledger.ledger as _ledger_mod
            orig_dir = _ledger_mod.SKILLS_DIR
            _ledger_mod.SKILLS_DIR = __import__("pathlib").Path(td)
            try:
                s = Skill(feature_key="TEST.serialization_roundtrip", precondition=pattern["precondition"],
                          transformation=pattern["transformation"],
                          provenance={"node_type": pattern["node_type"], "enclosing_call": pattern["enclosing_call"]})
                # store enclosing_call alongside node_type in provenance for this test skill,
                # since apply_skill() reads it from the top-level pattern dict normally --
                # here we just confirm the round-trip preserves the value, wherever stored.
                s.save_new_version()
                reloaded = Skill.load_latest("TEST.serialization_roundtrip")
                check("SERIALIZATION: enclosing_call survives ledger write/reload",
                      reloaded is not None and reloaded.provenance.get("enclosing_call") == "sorted")
            finally:
                _ledger_mod.SKILLS_DIR = orig_dir

    # Case 4: identical candidates -> no transformation (nothing to learn).
    identical_pattern = DE.extract_transformation(passing_real, passing_real, "winner_with_score")
    check("identical inputs produce no transformation (None)", identical_pattern is None)

    # Case 5: unalignable candidates (totally different structure) -> honest None,
    # not a forced/garbage diff.
    unalignable_a = "def winner_with_score(entries):\n    return max(entries, key=lambda x: x[1])[0], 0"
    unalignable_b = (
        "def winner_with_score(entries):\n"
        "    best = None\n"
        "    for e in entries:\n"
        "        if best is None or e[1] > best[1]:\n"
        "            best = e\n"
        "    return best[0], best[1]"
    )
    unalignable_pattern = DE.extract_transformation(unalignable_a, unalignable_b, "winner_with_score")
    check("structurally unalignable candidates honestly return None", unalignable_pattern is None)

    # Case 6: applying a skill to code where the precondition never matches ->
    # honest None (no silent no-op success).
    if pattern:
        already_correct = passing_real
        result = DE.apply_skill(already_correct, "winner_with_score", pattern)
        check("applying to already-correct code (no matching precondition) returns None",
              result is None)

    print()
    n_fail = sum(1 for _, ok in _checks if not ok)
    print(f"{len(_checks) - n_fail}/{len(_checks)} checks passed.")
    if n_fail:
        sys.exit(1)
    print("verify_diff_extract.py: ALL CHECKS PASSED.")


if __name__ == "__main__":
    main()
