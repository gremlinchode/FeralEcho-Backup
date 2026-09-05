#!/usr/bin/env python3
"""
STRICTLY READ-ONLY forensic replay. Reads real Tier-4 raw result records
(audits/tier4_apparatus/{stage1,stage2}_results.jsonl) and the real,
unmodified Tier-5 implementation (app/core/river_deliberation.py), and
computes a deterministic counterfactual: what would detect_full_agreement()
/ find_missing_agreed_definitions() / select_best_fallback_candidate()
have done to each real historical ARCH_COUNCIL (primary) and BASE_N
(secondary) synthesis event.

Writes NO output back into any Tier-4 file. All output goes to a new,
separate JSON file (scratchpad) and this script's own stdout. Makes
ZERO new LLM/model calls -- only real sandbox re-execution of
already-generated candidate code (the same objective_verify() used for
the original Tier-4 scoring), which is deterministic re-verification,
not new generation.

IMPORTANT METHODOLOGY NOTE, stated explicitly rather than glossed over:
real production deliberate_and_learn() builds its `opinions` dict keyed
by bare model name (opinions[model] = response). This is exactly what
this replay does for ARCH_COUNCIL, whose real observed composition
(qwen2.5-coder:7b, mlx:qwen3, echo:latest) never repeats a model name
within one council, so no collision occurs. BASE_N is a HARNESS-ONLY
construct with no real production analog -- run_condition_basen() uses
the SAME model 3 times and stores attempts in a LIST, never a dict, for
exactly this reason. Feeding BASE_N's 3 same-model attempts through a
dict-shaped API (as Tier-5's real functions require) means a bare
model-name key would silently collapse 3 entries into 1 -- a REAL,
notable observation in its own right (the current implementation
implicitly assumes councillors have unique model identities), not
merely a scripting inconvenience. This replay uses index-qualified keys
(f"{model}#{i}") for BASE_N specifically so its 3 attempts are not lost,
and reports BASE_N results as SECONDARY / not a literal production
analog, exactly as the report accompanying this script must state.
"""
import json
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

import run_capability_pilot as base_pilot  # noqa: E402 (objective_verify, clean_code -- read-only reuse)
import app.core.river_deliberation as rd  # noqa: E402 (the REAL, unmodified Tier-5 functions)

TIER4_DIR = "audits/tier4_apparatus"


def load_stage_records(stage_num: int) -> list:
    path = f"{TIER4_DIR}/stage{stage_num}_results.jsonl"
    with open(path) as f:
        return [json.loads(l) for l in f]


def load_stage_suite(stage_num: int) -> dict:
    path = f"{TIER4_DIR}/tier4_stage{stage_num}_task_suite.json"
    with open(path) as f:
        return {t["task_id"]: t for t in json.load(f)["tasks"]}


def build_opinions_arch_council(record: dict) -> dict:
    """Councillor calls only -- mechanism_calls[1:-1], skipping the
    warm-up (index 0) and the synthesis call (last index). Keyed by real
    model name, exactly matching real production's own opinions dict
    shape -- verified safe: this Tier-4 run's real composition
    (qwen2.5-coder:7b, mlx:qwen3, echo:latest) never repeats a model
    within one council."""
    calls = record["mechanism_calls"][1:-1]
    return {c["model"]: c["response_text"] for c in calls}


def build_opinions_basen(record: dict) -> dict:
    """Attempt calls only -- mechanism_calls[:-1]. Index-qualified keys
    (see module docstring) -- BASE_N is a harness-only construct with no
    real production dict-keyed analog; this preserves all 3 same-model
    attempts rather than silently collapsing them."""
    calls = record["mechanism_calls"][:-1]
    return {f"{c['model']}#{i}": c["response_text"] for i, c in enumerate(calls)}


def historical_synthesis_text(record: dict) -> str:
    """The raw text the real synthesis call actually returned -- this IS
    raw_response for both arms (deliberate_and_learn()/run_condition_basen()
    both return the synthesis call's own output directly)."""
    return record["raw_response"]


def replay_one_event(record: dict, opinions: dict, test_code: str) -> dict:
    """Deterministic counterfactual for one real historical event. Uses
    the REAL, unmodified river_deliberation functions -- no reimplemented
    logic, no new correctness criterion invented for this replay."""
    out = {
        "task_id": record["task_id"], "arm": record["arm"], "stage": record["stage"],
        "historical_passed": record["passed"],
        "historical_classification": record["classification"],
        "candidate_count": len(opinions),
    }

    # --- Historical reality: per-candidate extraction/parse status ---
    per_candidate = {}
    for key, text in opinions.items():
        extracted = rd._extract_candidate_code(text)
        parses = rd._ast_normalize(extracted) is not None if extracted is not None else False
        per_candidate[key] = {
            "extraction_succeeded": extracted is not None,
            "parses": parses,
            "top_level_names": sorted(rd._extract_top_level_names(extracted)) if extracted and parses else [],
        }
    out["per_candidate"] = per_candidate
    out["all_candidates_parse"] = all(v["parses"] for v in per_candidate.values())

    hist_synth_text = historical_synthesis_text(record)
    hist_synth_extracted = rd._extract_candidate_code(hist_synth_text)
    hist_synth_parses = rd._ast_normalize(hist_synth_extracted) is not None if hist_synth_extracted else False
    out["historical_synthesis_parses"] = hist_synth_parses
    out["historical_synthesis_top_level_names"] = (
        sorted(rd._extract_top_level_names(hist_synth_extracted)) if hist_synth_extracted and hist_synth_parses else []
    )

    # --- Counterfactual step 1: full agreement? ---
    agreed_code = rd.detect_full_agreement(opinions)
    out["would_detect_full_agreement"] = agreed_code is not None

    if agreed_code is not None:
        out["counterfactual_path"] = "full_agreement_shortcut"
        counterfactual_code = agreed_code
    else:
        # --- Counterfactual step 2: would completeness check reject the
        # ACTUAL historical synthesis output? ---
        missing = rd.find_missing_agreed_definitions(opinions, hist_synth_text)
        out["completeness_check_missing_names"] = sorted(missing)
        if missing:
            out["counterfactual_path"] = "completeness_fallback"
            counterfactual_code = rd.select_best_fallback_candidate(opinions)
        else:
            out["counterfactual_path"] = "synthesis_accepted_unchanged"
            counterfactual_code = hist_synth_text

    # --- Re-verify the counterfactual output against the REAL historical
    # test_code, using the SAME objective_verify() the original Tier-4
    # scoring used. This is the historical evaluator, not a new one. ---
    counterfactual_extracted_code = base_pilot.clean_code(counterfactual_code)
    verify = base_pilot.objective_verify(counterfactual_extracted_code, test_code)
    out["counterfactual_passed"] = verify["passed"]

    if out["historical_passed"] and out["counterfactual_passed"]:
        out["delta"] = "unchanged_pass"
    elif (not out["historical_passed"]) and out["counterfactual_passed"]:
        out["delta"] = "failure_intercepted"
    elif out["historical_passed"] and (not out["counterfactual_passed"]):
        out["delta"] = "regression"
    else:
        out["delta"] = "unchanged_fail"

    return out


def main():
    all_results = {"ARCH_COUNCIL": [], "BASE_N": []}
    for stage_num in (1, 2):
        records = load_stage_records(stage_num)
        suite = load_stage_suite(stage_num)
        for r in records:
            if r["arm"] not in ("ARCH_COUNCIL", "BASE_N"):
                continue
            test_code = suite[r["task_id"]]["test_code"]
            if r["arm"] == "ARCH_COUNCIL":
                opinions = build_opinions_arch_council(r)
            else:
                opinions = build_opinions_basen(r)
            result = replay_one_event(r, opinions, test_code)
            all_results[r["arm"]].append(result)
            print(f"[{r['stage']}] {r['task_id']:8s} {r['arm']:14s} "
                  f"hist_passed={result['historical_passed']!s:5s} "
                  f"cf_path={result['counterfactual_path']:26s} "
                  f"cf_passed={result['counterfactual_passed']!s:5s} "
                  f"delta={result['delta']}")

    out_path = "/tmp/tier5_counterfactual_replay_raw.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nFull raw replay data written to {out_path} (NOT a Tier-4 artifact, scratch only)")

    for arm in ("ARCH_COUNCIL", "BASE_N"):
        events = all_results[arm]
        n = len(events)
        hist_pass = sum(1 for e in events if e["historical_passed"])
        cf_pass = sum(1 for e in events if e["counterfactual_passed"])
        shortcuts = sum(1 for e in events if e["counterfactual_path"] == "full_agreement_shortcut")
        fallbacks = sum(1 for e in events if e["counterfactual_path"] == "completeness_fallback")
        unchanged_synth = sum(1 for e in events if e["counterfactual_path"] == "synthesis_accepted_unchanged")
        intercepted = sum(1 for e in events if e["delta"] == "failure_intercepted")
        regressions = sum(1 for e in events if e["delta"] == "regression")
        unchanged_pass = sum(1 for e in events if e["delta"] == "unchanged_pass")
        unchanged_fail = sum(1 for e in events if e["delta"] == "unchanged_fail")
        print(f"\n{'='*70}\n{arm} SUMMARY (n={n})\n{'='*70}")
        print(f"  historical pass rate: {hist_pass}/{n} ({100*hist_pass/n:.1f}%)")
        print(f"  counterfactual pass rate: {cf_pass}/{n} ({100*cf_pass/n:.1f}%)")
        print(f"  full_agreement_shortcut fired: {shortcuts}/{n} ({100*shortcuts/n:.1f}%)")
        print(f"  completeness_fallback fired: {fallbacks}/{n} ({100*fallbacks/n:.1f}%)")
        print(f"  synthesis_accepted_unchanged: {unchanged_synth}/{n} ({100*unchanged_synth/n:.1f}%)")
        print(f"  failures intercepted (FAIL->PASS): {intercepted}")
        print(f"  regressions (PASS->FAIL): {regressions}")
        print(f"  unchanged pass: {unchanged_pass}, unchanged fail: {unchanged_fail}")
        net = cf_pass - hist_pass
        print(f"  NET counterfactual pass-rate change: {net:+d} candidates ({100*net/n:+.1f}pp)")


if __name__ == "__main__":
    main()
