"""
PROTOCOL Section 5 -- generates the new, disjoint-seeded held-out panel for
the restart-persistence experiment, using genuinely NEW code content never
present in VECT's TRAIN or original held-out sets.

Does NOT edit historical_difficulty_calibration/tasks.py on disk (doing so
would silently change what a future re-run of VECT's own already-frozen
experiment produces for its own already-used seeds, since random.choice's
result depends on sequence length -- see PROTOCOL.md Section 5). Instead,
imports tasks.py fresh in this script's own process and monkeypatches its
CODE_SNIPPETS_COMPLEX list in-memory only, for the duration of this one
generation call.

Run once. Refuses to regenerate if the commitment file already exists
(same discipline as VECT's own cmd_seal).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[0] / "historical_difficulty_calibration"))
import tasks as T  # noqa: E402

OUT_DIR = _HERE.parents[2] / "memory" / "experiments" / "restart_persistence_transfer"

SEEDS = list(range(2000, 2010))  # 10 instances
LEVEL = 3
PREFIX = "restart_"

_ALL_PRIOR_SEEDS = set(
    list(range(700, 705)) + list(range(800, 805)) + list(range(810, 815)) +
    list(range(820, 825)) + list(range(830, 835)) + list(range(840, 845)) +
    list(range(850, 855)) + list(range(1000, 1008)) + list(range(1100, 1110))
)

# Genuinely new code content: never present anywhere in VECT's own
# CODE_SNIPPETS_SIMPLE, CODE_SNIPPETS_COMPLEX, train_tasks.json, or
# heldout_tasks.json. Structurally analogous to VECT's 4 "complex" openings
# (decorator / docstring / bare-import+def / from-import+decorator) so the
# difficulty structure P's clauses were written against is preserved,
# without reusing any of VECT's literal code.
NEW_CODE_SNIPPETS_COMPLEX = [
    "@staticmethod\ndef negate(x):\n    return -x",
    "\"\"\"Helper function.\"\"\"\ndef increment(x):\n    return x + 1",
    "import statistics\n\n\ndef average(nums):\n    return statistics.mean(nums)",
    "from functools import reduce\n\n\n@staticmethod\ndef product(nums):\n    return reduce(lambda a, b: a * b, nums, 1)",
]


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
    tmp.replace(path)


def _verify_disjoint_from_vect(new_snippets: "list[str]") -> None:
    """Grep-check: none of the new code strings appear anywhere in VECT's
    own TRAIN, held-out, or generator-bank content. Aborts loudly on any
    overlap rather than silently proceeding."""
    vect_dir = _HERE.parents[2] / "memory" / "experiments" / "validated_experience_competence_transfer"
    haystacks = []
    for fname in ("train_tasks.json", "heldout_tasks.json"):
        p = vect_dir / fname
        if p.exists():
            haystacks.append(p.read_text())
    haystacks.append(str(T.CODE_SNIPPETS_SIMPLE))
    haystacks.append(str(T.CODE_SNIPPETS_COMPLEX))
    combined = "\n".join(haystacks)
    for snippet in new_snippets:
        if snippet in combined:
            raise SystemExit(
                f"APPARATUS FAILURE -- new snippet is NOT actually new, found in "
                f"VECT's own artifacts:\n{snippet!r}"
            )
    print(f"Verified: all {len(new_snippets)} new code snippets are absent from "
          f"VECT's TRAIN, held-out set, and generator banks.")


def main():
    commitment_path = OUT_DIR / "restart_heldout_commitment.sha256"
    if commitment_path.exists():
        print("Already sealed -- refusing to regenerate. Delete the output dir by "
              "hand first for a genuine re-seal.")
        return

    seed_set = set(SEEDS)
    overlap = seed_set & _ALL_PRIOR_SEEDS
    if overlap:
        raise SystemExit(f"APPARATUS FAILURE: seed overlap detected with prior "
                          f"experiments: {overlap}")

    _verify_disjoint_from_vect(NEW_CODE_SNIPPETS_COMPLEX)

    # Monkeypatch in-process only -- tasks.py on disk is never touched.
    original_bank = T.CODE_SNIPPETS_COMPLEX
    T.CODE_SNIPPETS_COMPLEX = NEW_CODE_SNIPPETS_COMPLEX
    try:
        restart_tasks = T.build_calibration_set(SEEDS, LEVEL, PREFIX)
    finally:
        T.CODE_SNIPPETS_COMPLEX = original_bank  # restore, defensive

    used_codes = {t["expected_code"] for t in restart_tasks}
    print(f"Generated {len(restart_tasks)} instances using {len(used_codes)} "
          f"distinct new code bodies (of {len(NEW_CODE_SNIPPETS_COMPLEX)} available).")

    _write_json(OUT_DIR / "restart_heldout_tasks.json", restart_tasks)

    commitment = T.sha256_of(restart_tasks)
    with open(commitment_path, "w") as f:
        f.write(commitment + "\n")

    print(f"Sealed. restart_heldout_commitment.sha256 = {commitment}")


if __name__ == "__main__":
    main()
