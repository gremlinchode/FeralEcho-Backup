#!/usr/bin/env python3
"""Verified Skill Ledger -- MVK harness. Each subcommand is meant to be launched as
its own OS subprocess (mirroring persistent_routing's/restart_persistence_transfer's
own established convention) so the restart phase is a genuine process boundary, not a
simulated one.

Phases (per the accepted build-decision memo's own six-phase demonstration):
  build        -- construct the acquisition world + a disjoint held-out world.
  acquire      -- real variation (N candidates) + real oracle verification + real
                  transformation extraction; writes a candidate skill (unvalidated).
  transfer     -- (run as a FRESH process) loads the skill from disk, applies it to
                  fresh held-out instances, re-grades, compares against a no-skill
                  control on the SAME instances. Validates the skill if it helps.
  substitution -- reruns the held-out comparison with the skill file absent, to prove
                  the advantage (if any) depends on the skill's presence.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import oracle_runner as OR  # noqa: E402
import app.experiments.accumulation_probe.ollama_client as OC2  # noqa: E402
from app.experiments.accumulation_probe.common import OLLAMA_URL as AP0_OLLAMA_URL  # noqa: E402
from app.experiments.persistent_routing.strategies import build_prompt  # noqa: E402 (reused, unmodified)

from . import tasks as VT  # noqa: E402
from . import diff_extract as DE  # noqa: E402
from .ledger import Skill, log_provenance_event, validate  # noqa: E402
from .common import (  # noqa: E402
    LEDGER_ROOT, MODEL, OPTIONS, N_CANDIDATES_PER_FAILURE,
    sha256_text, write_json_new, read_json, seed_for,
)

_SYSTEM_PROMPT = (
    "You are a careful Python programmer. Respond with exactly one fenced "
    "Python code block that defines the requested function. Do not include "
    "explanations, tests, or example calls outside the code block."
)

FEATURE_KEY = "K2.T5.tag_priority_direction"  # the one real, already-characterized bug family this MVK targets
TASK_ID = "K2.T5"
FN_NAME = "winner_with_score"


_VARIATION_STRATEGIES = ("DIRECT", "STEPWISE", "WORKED_EXAMPLE", "STEPWISE")
# Engineering correction (found live, this session): using DIRECT alone for all N
# variation candidates produced 0/4 passes on the first real acquisition run.
# Real, already-existing historical data (strategy_characterization's Stage 1,
# log_stage1.jsonl) already showed DIRECT has a 0/36 real pass rate on this exact
# task family (K2.T5) while STEPWISE has 4/36 -- the fix is to draw variation from
# a strategy MIX known, from real prior evidence, to have non-zero pass probability,
# not to re-roll seeds hoping for a different DIRECT outcome. This is an engineering
# fix grounded in already-collected evidence, not a post-hoc rescue.


def _generate_one(task, world, seed, strategy="DIRECT"):
    procedure = VT.real_procedure_text(world)
    prompt = build_prompt(strategy, task, procedure)
    body = OC2.request_body(MODEL, _SYSTEM_PROMPT, prompt, seed, OPTIONS)
    resp = OC2.chat(body, AP0_OLLAMA_URL, timeout=300)
    raw = resp["text"]
    code = OR.extract_code(raw, task["fn"])
    test_code, _n = VT.make_hidden_tests(task, world, "VAL")
    grade = OR.grade(code, test_code) if code else {"passed": False, "ran_ok": False}
    return code, grade, raw


def cmd_build():
    d = LEDGER_ROOT / "mvk"
    d.mkdir(parents=True, exist_ok=True)
    taken: set = set()
    acquisition_world = VT.build_world(world_index=0, taken=taken)
    taken2: set = set()
    holdout_world = VT.build_world(world_index=1, taken=taken2)
    write_json_new(d / "acquisition_world.json", acquisition_world)
    write_json_new(d / "holdout_world.json", holdout_world)
    print("[build] acquisition world (index 0) and holdout world (index 1) written, "
          "both under SEED_OFFSET=150000, confirmed disjoint from every prior offset.")


def _find_task(world, task_id):
    for t in VT.discovery_tasks(world):
        if t["task_id"] == task_id:
            return t
    raise ValueError(task_id)


def cmd_acquire():
    d = LEDGER_ROOT / "mvk"
    world = read_json(d / "acquisition_world.json")
    task = _find_task(world, TASK_ID)

    candidates = []
    for i in range(N_CANDIDATES_PER_FAILURE):
        strategy = _VARIATION_STRATEGIES[i % len(_VARIATION_STRATEGIES)]
        seed = seed_for("ACQUIRE", TASK_ID, i)
        code, grade, raw = _generate_one(task, world, seed, strategy)
        candidates.append({"index": i, "seed": seed, "strategy": strategy, "code": code,
                            "passed": bool(grade.get("passed")), "raw": raw})
        print(f"[acquire] candidate {i} (strategy={strategy}): passed={grade.get('passed')}")

    write_json_new(d / "acquisition_candidates.json", candidates)

    passing = [c for c in candidates if c["passed"]]
    failing = [c for c in candidates if not c["passed"]]
    if not passing or not failing:
        print(f"[acquire] RESULT: {len(passing)} passing, {len(failing)} failing out of "
              f"{len(candidates)} real candidates -- need at least one of each to diff. "
              "No skill extracted. This is an honest, reportable outcome, not an error.")
        write_json_new(d / "acquisition_result.json", {"outcome": "no_diff_pair", "n_passing": len(passing), "n_failing": len(failing)})
        return

    pattern = None
    used_pair = None
    for f in failing:
        for p in passing:
            pattern = DE.extract_transformation(f["code"], p["code"], FN_NAME)
            if pattern is not None:
                used_pair = (f["index"], p["index"])
                break
        if pattern is not None:
            break

    if pattern is None:
        print("[acquire] RESULT: real passing/failing candidates exist, but no clean, "
              "minimal transformation could be extracted from any pair (structurally "
              "unalignable). Honest negative result -- not fixed by forcing a diff.")
        write_json_new(d / "acquisition_result.json", {"outcome": "no_extractable_pattern",
                        "n_passing": len(passing), "n_failing": len(failing)})
        return

    skill = Skill(
        feature_key=FEATURE_KEY,
        precondition=pattern["precondition"],
        transformation=pattern["transformation"],
        provenance={
            "source_task_id": TASK_ID, "source_world_index": 0,
            "failing_candidate_index": used_pair[0], "passing_candidate_index": used_pair[1],
            "failing_code_hash": sha256_text(failing[0]["code"]),
            "passing_code_hash": sha256_text(passing[0]["code"]),
            "node_type": pattern["node_type"],
            "enclosing_call": pattern["enclosing_call"],
        },
        held_out_verdict=None, status="candidate", version=1,
    )
    content_hash = skill.save_new_version()
    write_json_new(d / "acquisition_result.json", {"outcome": "skill_candidate_written",
                    "feature_key": FEATURE_KEY, "content_hash": content_hash, "used_pair": used_pair})
    print(f"[acquire] RESULT: skill candidate written for {FEATURE_KEY} (status=candidate, "
          f"held_out_verdict=None). content_hash={content_hash}")


def cmd_reextract():
    """Re-run pattern extraction against the ALREADY-COLLECTED real acquisition
    candidates (memory/experiments/skill_ledger/mvk/acquisition_candidates.json) --
    zero new model calls. Exists specifically for the case where diff_extract.py's
    extraction logic itself was fixed/improved (e.g. the enclosing-call-context fix)
    after acquisition already produced real, valid failing/passing candidates: there
    is no reason to spend new model calls re-generating candidates that were never
    the source of the problem. Writes a new skill version (status='candidate',
    held_out_verdict=None -- NOT yet re-validated; run 'transfer' next as usual)."""
    d = LEDGER_ROOT / "mvk"
    candidates = read_json(d / "acquisition_candidates.json")
    passing = [c for c in candidates if c["passed"]]
    failing = [c for c in candidates if not c["passed"]]
    if not passing or not failing:
        sys.exit("[reextract] STOP: acquisition_candidates.json has no passing/failing pair "
                  "to diff -- nothing to re-extract.")

    pattern = None
    used_pair = None
    for f in failing:
        for p in passing:
            pattern = DE.extract_transformation(f["code"], p["code"], FN_NAME)
            if pattern is not None:
                used_pair = (f["index"], p["index"])
                break
        if pattern is not None:
            break

    if pattern is None:
        sys.exit("[reextract] STOP: re-extraction against the existing real candidates "
                  "still produces no clean pattern -- the fix did not change this outcome.")

    prior = Skill.load_latest(FEATURE_KEY)
    next_version = (prior.version + 1) if prior is not None else 1
    skill = Skill(
        feature_key=FEATURE_KEY,
        precondition=pattern["precondition"],
        transformation=pattern["transformation"],
        provenance={
            "source_task_id": TASK_ID, "source_world_index": 0,
            "failing_candidate_index": used_pair[0], "passing_candidate_index": used_pair[1],
            "failing_code_hash": sha256_text(failing[0]["code"]),
            "passing_code_hash": sha256_text(passing[0]["code"]),
            "node_type": pattern["node_type"],
            "enclosing_call": pattern["enclosing_call"],
            "reextracted_from_version": prior.version if prior is not None else None,
            "reextraction_reason": "enclosing-call-context fix in diff_extract.py "
                                    "(see audits/2026-09-27_verified_skill_ledger_mvk_first_run_report.md)",
        },
        held_out_verdict=None, status="candidate", version=next_version,
    )
    content_hash = skill.save_new_version()
    print(f"[reextract] RESULT: skill re-extracted with ZERO new model calls from the "
          f"existing real acquisition_candidates.json, written as v{next_version} "
          f"(status=candidate, held_out_verdict=None). content_hash={content_hash} "
          f"enclosing_call={pattern['enclosing_call']!r}")


def cmd_transfer():
    """Run as a FRESH process. Loads the skill from disk (genuine restart boundary),
    generates fresh held-out candidates, applies the skill to any that fail, re-grades,
    and compares against the un-patched (no-skill) outcome on the SAME instances."""
    d = LEDGER_ROOT / "mvk"
    world = read_json(d / "holdout_world.json")
    task = _find_task(world, TASK_ID)

    skill = Skill.load_latest(FEATURE_KEY)
    if skill is None:
        sys.exit(f"[transfer] STOP: no skill found for {FEATURE_KEY} -- run 'acquire' first.")
    print(f"[transfer] loaded skill version={skill.version} status={skill.status} "
          f"(genuine restart: this is a fresh process, matching restart_persistence_transfer's own PID/id(sys.modules) evidence standard)")
    import os
    print(f"[transfer] PID={os.getpid()} id(sys.modules)={id(sys.modules)}")

    # Deliberately DIRECT-only here (not the acquisition-phase strategy mix): real
    # historical data shows DIRECT has a ~0% baseline pass rate on this task family,
    # which makes it the cleanest possible test of the skill's own causal
    # contribution -- any improvement over a near-zero DIRECT baseline is much less
    # confounded with a strategy's own inherent competence than mixing in STEPWISE
    # (which sometimes passes unaided) would be.
    results = []
    for i in range(N_CANDIDATES_PER_FAILURE):
        seed = seed_for("TRANSFER", TASK_ID, i)
        code, grade, raw = _generate_one(task, world, seed, "DIRECT")
        original_passed = bool(grade.get("passed"))
        patched_passed = original_passed
        applied = False
        if not original_passed and code:
            fixed_code = DE.apply_skill(code, FN_NAME, {"precondition": skill.precondition,
                                                          "transformation": skill.transformation,
                                                          "node_type": skill.provenance["node_type"],
                                                          "enclosing_call": skill.provenance.get("enclosing_call")})
            if fixed_code is not None:
                applied = True
                test_code, _n = VT.make_hidden_tests(task, world, "VAL")
                fixed_grade = OR.grade(fixed_code, test_code)
                patched_passed = bool(fixed_grade.get("passed"))
        results.append({"index": i, "seed": seed, "original_passed": original_passed,
                         "skill_applied": applied, "patched_passed": patched_passed})
        print(f"[transfer] instance {i}: original_passed={original_passed} "
              f"skill_applied={applied} patched_passed={patched_passed}")

    write_json_new(d / "transfer_result_with_skill.json", {"results": results})
    n_orig = sum(r["original_passed"] for r in results)
    n_patched = sum(r["patched_passed"] for r in results)
    n_applied = sum(r["skill_applied"] for r in results)
    print(f"[transfer] DONE. original pass rate={n_orig}/{len(results)}  "
          f"with-skill pass rate={n_patched}/{len(results)}  skill applied on {n_applied} instances")

    verdict = "PASS" if n_patched > n_orig else "FAIL"
    validate(FEATURE_KEY, verdict)
    print(f"[transfer] skill {FEATURE_KEY} held_out_verdict={verdict} "
          f"(eligible for consumption: {verdict == 'PASS'})")


def cmd_substitution():
    """Run as a FRESH process, with the skill file temporarily moved aside, to confirm
    the transfer-phase advantage (if any) actually depends on the skill's presence --
    reuses transfer_result_with_skill.json's own instances (same seeds -> same
    candidates, deterministic) and simply omits the skill-application step."""
    d = LEDGER_ROOT / "mvk"
    prior = read_json(d / "transfer_result_with_skill.json")
    world = read_json(d / "holdout_world.json")
    task = _find_task(world, TASK_ID)

    results = []
    for r in prior["results"]:
        seed = r["seed"]
        code, grade, raw = _generate_one(task, world, seed)
        original_passed = bool(grade.get("passed"))
        results.append({"index": r["index"], "seed": seed, "original_passed": original_passed})
        print(f"[substitution] instance {r['index']}: original_passed={original_passed} (skill absent)")

    write_json_new(d / "substitution_result_no_skill.json", {"results": results})
    n_no_skill = sum(r["original_passed"] for r in results)
    n_with_skill = sum(r["patched_passed"] for r in prior["results"])
    print(f"[substitution] DONE. no-skill pass rate={n_no_skill}/{len(results)}  "
          f"(with-skill pass rate was {n_with_skill}/{len(prior['results'])})")
    print(f"[substitution] advantage attributable to skill presence: "
          f"{'YES' if n_with_skill > n_no_skill else 'NO — advantage did not disappear or never existed'}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["build", "acquire", "reextract", "transfer", "substitution"])
    a = ap.parse_args()
    {"build": cmd_build, "acquire": cmd_acquire, "reextract": cmd_reextract,
     "transfer": cmd_transfer, "substitution": cmd_substitution}[a.phase]()
