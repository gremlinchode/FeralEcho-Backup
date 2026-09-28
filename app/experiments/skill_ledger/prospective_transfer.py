#!/usr/bin/env python3
"""Prospective, coverage-qualified causal transfer test for the already-acquired,
already-fixed (enclosing-call-context) skill `K2.T5.tag_priority_direction`.

Governing, FROZEN protocol (read before touching this file):
  audits/2026-09-27_vsl_prospective_causal_transfer_protocol.md

Three subcommands, each meant to run as its own OS subprocess (same convention as
harness.py's build/acquire/transfer/substitution):

  select        -- Phase 5. Generates up to 20 fresh STEPWISE candidates against the
                   existing disjoint holdout world, admits a candidate to the test set
                   ONLY on a mechanical, non-executing precondition match (apply_skill()
                   returning non-None) -- never on oracle pass/fail. Stops at 4 eligible
                   or the 20-candidate cap. Freezes the selected set to disk BEFORE any
                   oracle outcome is revealed anywhere (printed or otherwise inspected).
  true          -- Phase 6 (run as a FRESH process). Loads the skill normally, runs the
                   frozen set through it, applies/re-grades where eligible.
  substitution  -- Phase 7 (run as a FRESH process). Regenerates the identical frozen
                   seeds with the skill never consulted at all -- the same "skill absent"
                   convention harness.py's own cmd_substitution() already established
                   (no application step is ever reached, rather than literally moving a
                   file aside).

This module does NOT modify diff_extract.py, ledger.py, or the frozen skill in any way.
It imports harness.py's already-tested generation/grading helpers rather than
reimplementing them.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from . import diff_extract as DE  # noqa: E402
from . import harness as H  # noqa: E402
from .ledger import Skill  # noqa: E402
from .common import LEDGER_ROOT, sha256_text, write_json_new, read_json, seed_for  # noqa: E402

TASK_ID = H.TASK_ID
FN_NAME = H.FN_NAME
FEATURE_KEY = H.FEATURE_KEY
STRATEGY = "STEPWISE"  # pre-registered in the frozen protocol, before any generation here
HARD_CAP = 20
TARGET_N = 4

PROSPECTIVE_DIR = LEDGER_ROOT / "prospective"


def _known_contaminant_hashes() -> set:
    """Every code hash this project has already generated/observed for this feature
    key -- the acquisition candidates themselves, plus every skill version's own
    recorded failing/passing hashes. Used only for the freshness/contamination check
    (Phase 3); never used to decide eligibility."""
    hashes = set()
    d = LEDGER_ROOT / "mvk"
    try:
        acq = read_json(d / "acquisition_candidates.json")
        for c in acq:
            if c.get("code"):
                hashes.add(sha256_text(c["code"]))
    except FileNotFoundError:
        pass
    skills_dir = LEDGER_ROOT / "skills"
    for p in skills_dir.glob(f"{FEATURE_KEY}.v*.json"):
        d2 = read_json(p)
        prov = d2.get("provenance", {})
        for k in ("failing_code_hash", "passing_code_hash"):
            if prov.get(k):
                hashes.add(prov[k])
    return hashes


def cmd_select():
    """Phase 5. Outcome-blind selection. See module docstring."""
    world = read_json(LEDGER_ROOT / "mvk" / "holdout_world.json")
    task = H._find_task(world, TASK_ID)

    skill = Skill.load_latest(FEATURE_KEY)
    if skill is None:
        sys.exit("[select] STOP: no skill found -- this protocol requires the "
                  "already-acquired skill to exist. Not proceeding.")
    if skill.version != 4:
        print(f"[select] NOTE: latest skill is v{skill.version}, not the v4 the frozen "
              f"protocol recorded. Proceeding with whatever load_latest() returns, per "
              f"the frozen protocol's own instruction that only a schema-migration "
              f"reextract is permitted -- this is NOT that, flag for review if version "
              f"drifted for any other reason.")
    pattern = {
        "precondition": skill.precondition,
        "transformation": skill.transformation,
        "node_type": skill.provenance["node_type"],
        "enclosing_call": skill.provenance.get("enclosing_call"),
    }
    print(f"[select] frozen skill: {FEATURE_KEY} v{skill.version} "
          f"content_hash={skill.content_hash()} enclosing_call={pattern['enclosing_call']!r}")

    known_hashes = _known_contaminant_hashes()
    print(f"[select] {len(known_hashes)} known prior code hashes loaded for contamination check.")

    inspected = []       # structural record only -- no grade referenced for selection
    outcomes = {}        # index -> grade dict, stored but not consulted/printed until after freeze
    selected_indices = []
    contamination = None

    for i in range(HARD_CAP):
        seed = seed_for("PROSPECTIVE", TASK_ID, i)
        code, grade, raw = H._generate_one(task, world, seed, STRATEGY)
        outcomes[i] = grade  # stored, NOT inspected/printed here

        if not code:
            inspected.append({"index": i, "seed": seed, "eligible": False,
                               "reason": "no_code_extracted", "code_hash": None})
            print(f"[select] candidate {i}: no code extracted -- ineligible (not a precondition question)")
            continue

        code_hash = sha256_text(code)
        if code_hash in known_hashes:
            contamination = {"index": i, "seed": seed, "code_hash": code_hash,
                              "mechanism": "generated code is byte-identical to a previously "
                                           "observed acquisition/skill-provenance code hash"}
            print(f"[select] CONTAMINATION at candidate {i}: code hash matches a previously "
                  f"seen hash. Stopping per Phase 3/Outcome D -- no further candidates generated.")
            break

        fixed = DE.apply_skill(code, FN_NAME, pattern)
        eligible = fixed is not None
        inspected.append({"index": i, "seed": seed, "eligible": eligible,
                           "reason": None if eligible else "precondition_did_not_match",
                           "code_hash": code_hash, "code": code})
        print(f"[select] candidate {i}: eligible={eligible} "
              f"(structural precondition match only -- oracle outcome not yet inspected)")

        if eligible:
            selected_indices.append(i)
        if len(selected_indices) >= TARGET_N:
            break

    PROSPECTIVE_DIR.mkdir(parents=True, exist_ok=True)

    # --- FREEZE POINT: write the selection to disk BEFORE any oracle outcome is
    # revealed anywhere below this line. ---
    frozen = {
        "feature_key": FEATURE_KEY, "skill_version": skill.version,
        "skill_content_hash": skill.content_hash(), "enclosing_call": pattern["enclosing_call"],
        "strategy": STRATEGY, "hard_cap": HARD_CAP, "target_n": TARGET_N,
        "n_inspected": len(inspected), "selected_indices": selected_indices,
        "contamination": contamination,
        "candidates": [{k: v for k, v in c.items() if k != "code"} for c in inspected],
    }
    write_json_new(PROSPECTIVE_DIR / "selection_frozen.json", frozen)
    print(f"[select] SELECTION FROZEN: {len(selected_indices)}/{TARGET_N} eligible found "
          f"among {len(inspected)} inspected (cap={HARD_CAP}). Written to "
          f"{PROSPECTIVE_DIR / 'selection_frozen.json'} before any outcome below is printed.")

    if contamination is not None:
        write_json_new(PROSPECTIVE_DIR / "contamination_report.json", contamination)
        sys.exit("[select] OUTCOME D: contamination detected. STOP. Do not run the causal "
                  "test. See contamination_report.json.")

    # Full candidate detail (code included) saved separately for provenance/replication --
    # written after the frozen summary above, not before.
    write_json_new(PROSPECTIVE_DIR / "selection_candidates_full.json", inspected)

    if len(selected_indices) < TARGET_N:
        # --- NOW it is safe to reveal outcomes: selection is closed either way. ---
        revealed = {i: bool(outcomes[i].get("passed")) for i in range(len(inspected))}
        write_json_new(PROSPECTIVE_DIR / "outcomes_revealed_outcome_c.json", revealed)
        print(f"[select] OUTCOME C: only {len(selected_indices)}/{TARGET_N} eligible "
              f"candidates found among {len(inspected)} inspected (cap={HARD_CAP} reached). "
              f"Coverage insufficient under the frozen rule. Not a success or failure of "
              f"the mechanism. Stopping -- no TRUE/SUBSTITUTION run.")
        return

    print(f"[select] {TARGET_N} eligible candidates frozen: indices {selected_indices}. "
          f"Proceed to 'true' (fresh process), then 'substitution' (fresh process).")


def cmd_true():
    """Phase 6, run as a FRESH process."""
    frozen = read_json(PROSPECTIVE_DIR / "selection_frozen.json")
    if frozen.get("contamination") is not None:
        sys.exit("[true] STOP: selection_frozen.json records contamination -- do not run.")
    selected = frozen["selected_indices"]
    if len(selected) < TARGET_N:
        sys.exit(f"[true] STOP: only {len(selected)}/{TARGET_N} eligible -- Outcome C, "
                  f"no causal test to run.")

    skill = Skill.load_latest(FEATURE_KEY)
    if skill.content_hash() != frozen["skill_content_hash"]:
        sys.exit(f"[true] STOP: loaded skill content_hash {skill.content_hash()} does not "
                  f"match the frozen protocol's recorded {frozen['skill_content_hash']} -- "
                  f"the skill was not held frozen as required. Report discrepancy.")
    pattern = {"precondition": skill.precondition, "transformation": skill.transformation,
               "node_type": skill.provenance["node_type"],
               "enclosing_call": skill.provenance.get("enclosing_call")}

    import os
    print(f"[true] loaded skill v{skill.version} content_hash={skill.content_hash()} "
          f"(genuine restart: fresh process) PID={os.getpid()} id(sys.modules)={id(sys.modules)}")

    world = read_json(LEDGER_ROOT / "mvk" / "holdout_world.json")
    task = H._find_task(world, TASK_ID)

    results = []
    for i in selected:
        seed = seed_for("PROSPECTIVE", TASK_ID, i)
        code, grade, raw = H._generate_one(task, world, seed, STRATEGY)
        original_passed = bool(grade.get("passed"))
        patched_passed = original_passed
        applied = False
        if not original_passed and code:
            fixed_code = DE.apply_skill(code, FN_NAME, pattern)
            if fixed_code is not None:
                applied = True
                test_code, _n = H.VT.make_hidden_tests(task, world, "VAL")
                fixed_grade = H.OR.grade(fixed_code, test_code)
                patched_passed = bool(fixed_grade.get("passed"))
        results.append({"index": i, "seed": seed, "original_passed": original_passed,
                         "skill_applied": applied, "patched_passed": patched_passed})
        print(f"[true] instance {i}: original_passed={original_passed} "
              f"skill_applied={applied} patched_passed={patched_passed}")

    write_json_new(PROSPECTIVE_DIR / "true_result.json", {"results": results})
    n_orig = sum(r["original_passed"] for r in results)
    n_patched = sum(r["patched_passed"] for r in results)
    n_applied = sum(r["skill_applied"] for r in results)
    print(f"[true] DONE. original pass rate={n_orig}/{len(results)}  "
          f"with-skill pass rate={n_patched}/{len(results)}  skill applied on {n_applied} instances")


def cmd_substitution():
    """Phase 7, run as a FRESH process, skill never consulted (same 'skill absent'
    convention as harness.py's own cmd_substitution())."""
    frozen = read_json(PROSPECTIVE_DIR / "selection_frozen.json")
    selected = frozen["selected_indices"]
    if len(selected) < TARGET_N:
        sys.exit(f"[substitution] STOP: only {len(selected)}/{TARGET_N} eligible -- Outcome C.")

    true_result = read_json(PROSPECTIVE_DIR / "true_result.json")

    world = read_json(LEDGER_ROOT / "mvk" / "holdout_world.json")
    task = H._find_task(world, TASK_ID)

    import os
    print(f"[substitution] fresh process, skill never loaded/consulted. "
          f"PID={os.getpid()} id(sys.modules)={id(sys.modules)}")

    results = []
    for r in true_result["results"]:
        i = r["index"]
        seed = r["seed"]
        code, grade, raw = H._generate_one(task, world, seed, STRATEGY)
        original_passed = bool(grade.get("passed"))
        results.append({"index": i, "seed": seed, "original_passed": original_passed})
        print(f"[substitution] instance {i}: original_passed={original_passed} (skill absent)")

    write_json_new(PROSPECTIVE_DIR / "substitution_result.json", {"results": results})
    n_no_skill = sum(r["original_passed"] for r in results)
    n_with_skill = sum(r["patched_passed"] for r in true_result["results"])
    print(f"[substitution] DONE. no-skill pass rate={n_no_skill}/{len(results)}  "
          f"(with-skill pass rate was {n_with_skill}/{len(true_result['results'])})")
    print(f"[substitution] advantage attributable to skill presence: "
          f"{'YES' if n_with_skill > n_no_skill else 'NO'}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["select", "true", "substitution"])
    a = ap.parse_args()
    {"select": cmd_select, "true": cmd_true, "substitution": cmd_substitution}[a.phase]()
