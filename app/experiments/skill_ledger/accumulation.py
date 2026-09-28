#!/usr/bin/env python3
"""Checkpoint 7 -- accumulated competence test. Does possessing and consuming verified
Skill A (K2.T5.tag_priority_direction) causally help acquire Skill B (K2.T2, a
different but mechanistically related feature key)?

Governing, FROZEN protocol (read before touching this file):
  audits/2026-09-27_vsl_accumulated_competence_protocol.md

Subcommands, each meant to run as its own OS subprocess where the protocol calls for a
genuine restart boundary:

  a_present         -- Phase 4, A-PRESENT condition (fresh process). Generates 8 K2.T2
                        candidates; for each failure, attempts Skill A's unmodified
                        apply_skill() as a repair step.
  a_absent          -- Phase 4, A-ABSENT condition (SEPARATE fresh process). Regenerates
                        the identical seeds; Skill A is never loaded or consulted.
  qualify_b         -- Phase 5. If a real fail/pass pair exists for K2.T2 (from either
                        condition's real oracle outcomes), diff-extract Skill B.
  restart_check_b   -- Phase 6 (fresh process). Confirms Skill B reloads from disk.
  transfer_b        -- Phase 7 (select/true/substitution sub-subcommands), Skill B's own
                        small prospective transfer test, mirroring prospective_transfer.py.

This module imports harness.py's and diff_extract.py's already-tested functions
verbatim; it does not modify either file or Skill A.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from . import diff_extract as DE  # noqa: E402
from . import harness as H  # noqa: E402
from .ledger import Skill  # noqa: E402
from .common import LEDGER_ROOT, sha256_text, write_json_new, read_json, seed_for  # noqa: E402

SKILL_A_KEY = "K2.T5.tag_priority_direction"
SKILL_A_EXPECTED_HASH = "a5408f732897df353eb9ad6c6d8d2390794319910dd2ff5a4bd9da28a833501d"

B_TASK_ID = "K2.T2"
B_FN_NAME = "rank_all"
B_WORLD_INDEX = 2  # fresh, disjoint from A's acquisition (0) and holdout (1) worlds
B_TRANSFER_WORLD_INDEX = 3  # fresh again for Phase 7, disjoint from all three prior worlds

N_BUDGET = 8
_STRATEGIES = ("DIRECT", "STEPWISE", "WORKED_EXAMPLE", "STEPWISE",
               "DIRECT", "STEPWISE", "WORKED_EXAMPLE", "STEPWISE")  # frozen, Phase 3

ACCUM_DIR = LEDGER_ROOT / "accumulation"


def _b_world():
    d = LEDGER_ROOT / "accumulation"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"world_{B_WORLD_INDEX}.json"
    if path.exists():
        return read_json(path)
    world = H.VT.build_world(world_index=B_WORLD_INDEX, taken=set())
    write_json_new(path, world)
    return world


def _load_skill_a():
    skill = Skill.load_latest(SKILL_A_KEY)
    if skill is None:
        sys.exit("[accum] STOP: Skill A not found in ledger.")
    if skill.content_hash() != SKILL_A_EXPECTED_HASH:
        sys.exit(f"[accum] STOP: Skill A content_hash {skill.content_hash()} does not match "
                  f"the frozen protocol's recorded {SKILL_A_EXPECTED_HASH} -- Skill A was not "
                  f"held frozen as required.")
    return skill


def _pattern_for(skill):
    return {"precondition": skill.precondition, "transformation": skill.transformation,
            "node_type": skill.provenance["node_type"],
            "enclosing_call": skill.provenance.get("enclosing_call")}


def cmd_a_present():
    """Phase 4, A-PRESENT, fresh process."""
    skill_a = _load_skill_a()
    pattern_a = _pattern_for(skill_a)
    import os
    print(f"[a_present] Skill A loaded: v{skill_a.version} content_hash={skill_a.content_hash()} "
          f"(genuine restart: fresh process) PID={os.getpid()} id(sys.modules)={id(sys.modules)}")

    world = _b_world()
    task = H._find_task(world, B_TASK_ID)

    results = []
    for i in range(N_BUDGET):
        seed = seed_for("ACQUIRE_B", B_TASK_ID, i)
        strategy = _STRATEGIES[i]
        code, grade, raw = H._generate_one(task, world, seed, strategy)
        original_passed = bool(grade.get("passed")) if code else False
        code_hash = sha256_text(code) if code else None
        skill_a_applied = False
        patched_passed = original_passed
        if code and not original_passed:
            fixed_code = DE.apply_skill(code, B_FN_NAME, pattern_a)
            if fixed_code is not None:
                skill_a_applied = True
                test_code, _n = H.VT.make_hidden_tests(task, world, "VAL")
                fixed_grade = H.OR.grade(fixed_code, test_code)
                patched_passed = bool(fixed_grade.get("passed"))
        results.append({"index": i, "seed": seed, "strategy": strategy, "code": code,
                         "code_hash": code_hash, "original_passed": original_passed,
                         "skill_a_applied": skill_a_applied, "patched_passed": patched_passed})
        print(f"[a_present] candidate {i} (strategy={strategy}): original_passed={original_passed} "
              f"skill_a_applied={skill_a_applied} patched_passed={patched_passed}")

    write_json_new(ACCUM_DIR / "a_present_result.json", {"results": results})
    n_orig = sum(r["original_passed"] for r in results)
    n_patched = sum(r["patched_passed"] for r in results)
    n_applied = sum(r["skill_a_applied"] for r in results)
    distinct_hashes = {r["code_hash"] for r in results if r["code_hash"]}
    distinct_pass_hashes = {r["code_hash"] for r in results if r["code_hash"] and r["patched_passed"]}
    print(f"[a_present] DONE. raw: original_pass={n_orig}/{N_BUDGET} patched_pass={n_patched}/{N_BUDGET} "
          f"skill_a_applied={n_applied}/{N_BUDGET}  distinct_code_bodies={len(distinct_hashes)}/{N_BUDGET} "
          f"distinct_code_bodies_passing={len(distinct_pass_hashes)}")


def cmd_a_absent():
    """Phase 4, A-ABSENT, SEPARATE fresh process -- Skill A never loaded/consulted."""
    import os
    print(f"[a_absent] fresh process, Skill A never loaded/consulted. "
          f"PID={os.getpid()} id(sys.modules)={id(sys.modules)}")

    world = _b_world()
    task = H._find_task(world, B_TASK_ID)

    results = []
    for i in range(N_BUDGET):
        seed = seed_for("ACQUIRE_B", B_TASK_ID, i)
        strategy = _STRATEGIES[i]
        code, grade, raw = H._generate_one(task, world, seed, strategy)
        original_passed = bool(grade.get("passed")) if code else False
        code_hash = sha256_text(code) if code else None
        results.append({"index": i, "seed": seed, "strategy": strategy, "code": code,
                         "code_hash": code_hash, "original_passed": original_passed})
        print(f"[a_absent] candidate {i} (strategy={strategy}): original_passed={original_passed} (skill A absent)")

    write_json_new(ACCUM_DIR / "a_absent_result.json", {"results": results})
    n_orig = sum(r["original_passed"] for r in results)
    distinct_hashes = {r["code_hash"] for r in results if r["code_hash"]}
    distinct_pass_hashes = {r["code_hash"] for r in results if r["code_hash"] and r["original_passed"]}
    print(f"[a_absent] DONE. original_pass={n_orig}/{N_BUDGET}  "
          f"distinct_code_bodies={len(distinct_hashes)}/{N_BUDGET} "
          f"distinct_code_bodies_passing={len(distinct_pass_hashes)}")


def cmd_qualify_b():
    """Phase 5. Attempts to diff-extract Skill B from whatever real fail/pass pair
    exists across BOTH conditions' real, already-computed results (a passing example
    may come from unaided generation in either condition, or from Skill A's repair in
    A-PRESENT -- diff_extract.extract_transformation() only needs one real failing
    example and one real passing example on the same task, it does not care which
    condition or mechanism produced the pass)."""
    present = read_json(ACCUM_DIR / "a_present_result.json")["results"]
    absent = read_json(ACCUM_DIR / "a_absent_result.json")["results"]

    # Build combined pools of (index-tagged) failing/passing CODE from both conditions.
    # For A-PRESENT, "passing" includes both original passes and skill-A-repaired passes
    # (the repaired CODE, not the original failing code, since that's the real passing
    # artifact) -- but repaired code is Skill A's OWN transformation applied, and diffing
    # Skill A's own output against a failing T2 candidate would just re-derive Skill A,
    # not a genuine independent Skill B. So repaired-via-Skill-A passes are EXCLUDED from
    # the pool used to extract Skill B -- only genuinely UNAIDED passes (from either
    # condition) are eligible passing examples, since only those represent T2's own
    # independently-solved logic, not Skill A's transformation re-applied.
    failing = [{"code": r["code"], "source": "a_present", "index": r["index"]}
               for r in present if r["code"] and not r["original_passed"]]
    failing += [{"code": r["code"], "source": "a_absent", "index": r["index"]}
                for r in absent if r["code"] and not r["original_passed"]]
    passing = [{"code": r["code"], "source": "a_present", "index": r["index"]}
               for r in present if r["code"] and r["original_passed"]]
    passing += [{"code": r["code"], "source": "a_absent", "index": r["index"]}
                for r in absent if r["code"] and r["original_passed"]]

    print(f"[qualify_b] pool: {len(failing)} unaided failing, {len(passing)} unaided passing "
          f"(candidates repaired by Skill A are deliberately excluded from this pool -- "
          f"extracting Skill B from Skill A's own transformation output would not be an "
          f"independent skill).")

    if not failing or not passing:
        write_json_new(ACCUM_DIR / "qualify_b_result.json",
                        {"outcome": "no_unaided_diff_pair", "n_failing": len(failing), "n_passing": len(passing)})
        print(f"[qualify_b] RESULT: {len(passing)} unaided passing, {len(failing)} unaided failing "
              f"-- need at least one of each to diff. No Skill B extracted from unaided pairs. "
              f"(Note: this does not mean Skill A didn't help -- see a_present/a_absent results "
              f"for the primary causal comparison, which is independent of B's own qualification.)")
        return

    pattern = None
    used_pair = None
    for f in failing:
        for p in passing:
            pattern = DE.extract_transformation(f["code"], p["code"], B_FN_NAME)
            if pattern is not None:
                used_pair = (f, p)
                break
        if pattern is not None:
            break

    if pattern is None:
        write_json_new(ACCUM_DIR / "qualify_b_result.json", {"outcome": "no_extractable_pattern"})
        print("[qualify_b] RESULT: real passing/failing candidates exist, but no clean, "
              "minimal transformation could be extracted (structurally unalignable). "
              "Honest negative result.")
        return

    skill_a = _load_skill_a()
    same_as_a = (pattern["precondition"] == skill_a.precondition and
                 pattern["transformation"] == skill_a.transformation)

    skill_b = Skill(
        feature_key="K2.T2.discovered_via_accumulation_test",
        precondition=pattern["precondition"], transformation=pattern["transformation"],
        provenance={
            "source_task_id": B_TASK_ID, "source_world_index": B_WORLD_INDEX,
            "failing_source": used_pair[0]["source"], "failing_index": used_pair[0]["index"],
            "passing_source": used_pair[1]["source"], "passing_index": used_pair[1]["index"],
            "failing_code_hash": sha256_text(used_pair[0]["code"]),
            "passing_code_hash": sha256_text(used_pair[1]["code"]),
            "node_type": pattern["node_type"], "enclosing_call": pattern["enclosing_call"],
            "identical_to_skill_a": same_as_a,
            "acquisition_context": "Checkpoint 7 accumulated-competence test -- see "
                                    "audits/2026-09-27_vsl_accumulated_competence_protocol.md",
        },
        held_out_verdict=None, status="candidate", version=1,
    )
    content_hash = skill_b.save_new_version()
    write_json_new(ACCUM_DIR / "qualify_b_result.json",
                    {"outcome": "skill_b_written", "feature_key": skill_b.feature_key,
                     "content_hash": content_hash, "identical_to_skill_a": same_as_a,
                     "used_pair": {"failing": used_pair[0], "passing": used_pair[1]}})
    print(f"[qualify_b] RESULT: Skill B written -- feature_key={skill_b.feature_key} "
          f"content_hash={content_hash} identical_to_skill_a={same_as_a}")
    if same_as_a:
        print("[qualify_b] NOTE: Skill B's extracted pattern is structurally IDENTICAL to "
              "Skill A's -- this is the same underlying bug pattern recurring in a second "
              "task, not a distinct second pattern. Reported honestly, not inflated.")


def cmd_restart_check_b():
    """Phase 6, fresh process."""
    skill = Skill.load_latest("K2.T2.discovered_via_accumulation_test")
    if skill is None:
        sys.exit("[restart_check_b] STOP: no Skill B found -- run qualify_b first.")
    import os
    print(f"[restart_check_b] Skill B reloaded: v{skill.version} content_hash={skill.content_hash()} "
          f"(genuine restart: fresh process) PID={os.getpid()} id(sys.modules)={id(sys.modules)}")
    write_json_new(ACCUM_DIR / "restart_check_b_result.json",
                    {"version": skill.version, "content_hash": skill.content_hash(),
                     "pid": os.getpid(), "id_sys_modules": id(sys.modules)})


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["a_present", "a_absent", "qualify_b", "restart_check_b"])
    a = ap.parse_args()
    {"a_present": cmd_a_present, "a_absent": cmd_a_absent,
     "qualify_b": cmd_qualify_b, "restart_check_b": cmd_restart_check_b}[a.phase]()
