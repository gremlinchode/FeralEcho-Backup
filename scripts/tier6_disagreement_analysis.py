#!/usr/bin/env python3
"""
STRICTLY READ-ONLY forensic analysis of candidate disagreement across the
full Tier-4 coding corpus. Reads real, already-captured Tier-4
mechanism_calls (raw candidate text, never regenerated) and the real,
unmodified Tier-5 functions. Makes ZERO new LLM/model calls. The only
"execution" performed is real, deterministic sandbox re-verification of
already-generated candidate code against the real, frozen test_code --
the same objective_verify() the original Tier-4 scoring used.

Writes no output back into any Tier-4/Tier-5 artifact. All output goes
to /tmp (scratch) and this script's own stdout.
"""
import json
import os
import sys
from collections import Counter

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

import run_capability_pilot as base_pilot  # noqa: E402
import app.core.river_deliberation as rd  # noqa: E402

TIER4_DIR = "audits/tier4_apparatus"


def load_stage_records(stage_num):
    with open(f"{TIER4_DIR}/stage{stage_num}_results.jsonl") as f:
        return [json.loads(l) for l in f]


def load_stage_suite(stage_num):
    with open(f"{TIER4_DIR}/tier4_stage{stage_num}_task_suite.json") as f:
        return {t["task_id"]: t for t in json.load(f)["tasks"]}


def candidate_calls(record):
    """Returns (opinions_dict, historical_synthesis_text) for one record."""
    if record["arm"] == "ARCH_COUNCIL":
        calls = record["mechanism_calls"][1:-1]
        opinions = {c["model"]: c["response_text"] for c in calls}
    else:  # BASE_N -- see prior audit's documented index-qualified-key caveat
        calls = record["mechanism_calls"][:-1]
        opinions = {f"{c['model']}#{i}": c["response_text"] for i, c in enumerate(calls)}
    return opinions, record["raw_response"]


def analyze_candidate(key, raw_text, test_code):
    extracted = rd._extract_candidate_code(raw_text)
    fingerprint = rd._ast_normalize(extracted) if extracted is not None else None
    names = rd._extract_top_level_names(extracted) if extracted and fingerprint else set()
    code = base_pilot.clean_code(raw_text)
    verify = base_pilot.objective_verify(code, test_code)
    return {
        "key": key,
        "raw_length": len(raw_text),
        "extracted_length": len(extracted) if extracted else 0,
        "extraction_succeeded": extracted is not None,
        "parses": fingerprint is not None,
        "ast_fingerprint": fingerprint,
        "top_level_names": sorted(names),
        "ran_ok": verify["ran_ok"],
        "passed": verify["passed"],
    }


def classify_event(candidates: list, hist_synth) -> dict:
    """Assigns a primary disagreement-type label plus supporting booleans,
    from the 15-category taxonomy requested. Categories are not mutually
    exclusive in reality (e.g. a candidate can be both "syntax-invalid"
    and part of a "some correct/some incorrect" split) -- this records
    the relevant flags rather than forcing one label."""
    n = len(candidates)
    fingerprints = [c["ast_fingerprint"] for c in candidates]
    non_null_fps = [f for f in fingerprints if f is not None]
    exact_texts = set()  # exact byte-for-byte on EXTRACTED code, stronger than AST
    parsing = [c for c in candidates if c["parses"]]
    correct = [c for c in candidates if c["passed"]]
    incorrect_but_ran = [c for c in candidates if c["ran_ok"] and not c["passed"]]
    syntax_invalid = [c for c in candidates if not c["parses"]]
    crashed = [c for c in candidates if not c["ran_ok"]]

    flags = {
        "n_candidates": n,
        "exact_agreement_all": len(set(fingerprints)) == 1 and None not in fingerprints,
        "ast_agreement_count": Counter(fingerprints).most_common(1)[0][1] if non_null_fps else 0,
        "all_syntax_valid": len(syntax_invalid) == 0,
        "any_syntax_invalid": len(syntax_invalid) > 0,
        "n_syntax_invalid": len(syntax_invalid),
        "n_crashed_or_errored": len(crashed),
        "n_correct": len(correct),
        "n_incorrect_but_ran": len(incorrect_but_ran),
        "all_correct": len(correct) == n,
        "all_incorrect": len(correct) == 0,
        "some_correct_some_incorrect": 0 < len(correct) < n,
        "exactly_one_correct": len(correct) == 1,
        "majority_correct": len(correct) > n / 2,
        "minority_correct": 0 < len(correct) <= n / 2,
    }

    # Primary label, in priority order (most specific / most informative first)
    if flags["exact_agreement_all"] and flags["all_correct"]:
        label = "exact_agreement_all_correct"
    elif flags["exact_agreement_all"] and flags["all_incorrect"]:
        label = "exact_agreement_all_incorrect"  # unanimous shared bug
    elif flags["all_correct"]:
        label = "textual_variation_all_correct"  # different text, all pass -- equivalent implementations or harmless variation
    elif flags["all_incorrect"] and flags["any_syntax_invalid"]:
        label = "all_incorrect_including_syntax_invalid"
    elif flags["all_incorrect"]:
        label = "all_incorrect_semantically"
    elif flags["exactly_one_correct"]:
        label = "exactly_one_correct_rest_wrong"
    elif flags["majority_correct"]:
        label = "majority_correct_minority_wrong"
    elif flags["minority_correct"]:
        label = "minority_correct_majority_wrong"
    else:
        label = "other"

    flags["label"] = label
    return flags


def main():
    all_events = []
    for stage_num in (1, 2):
        records = load_stage_records(stage_num)
        suite = load_stage_suite(stage_num)
        for r in records:
            if r["arm"] not in ("ARCH_COUNCIL", "BASE_N"):
                continue
            test_code = suite[r["task_id"]]["test_code"]
            opinions, hist_synth_text = candidate_calls(r)
            candidates = [analyze_candidate(k, v, test_code) for k, v in opinions.items()]
            event_flags = classify_event(candidates, hist_synth_text)

            hist_synth_extracted = rd._extract_candidate_code(hist_synth_text)
            hist_synth_fp = rd._ast_normalize(hist_synth_extracted) if hist_synth_extracted else None

            # Simulate 4 selection strategies among the candidates, purely
            # deterministically -- what each WOULD pick, and whether that
            # pick is correct. None of these make a new model call; all
            # operate on already-generated text.
            def by_length(cands, key_field="raw_length", reverse=True):
                pool = [c for c in cands if c["parses"]] or cands
                return max(pool, key=lambda c: c[key_field] if not reverse else c[key_field])

            longest_parsing = max([c for c in candidates if c["parses"]] or candidates,
                                   key=lambda c: c["raw_length"])
            shortest_parsing = min([c for c in candidates if c["parses"]] or candidates,
                                    key=lambda c: c["raw_length"])
            # Majority-structural-similarity: prefer whichever candidate's
            # fingerprint is shared by the most OTHER candidates (ties broken
            # by length) -- a candidate alternative to length-based fallback,
            # evaluated here for comparison, not yet implemented anywhere.
            fp_counts = Counter(c["ast_fingerprint"] for c in candidates if c["ast_fingerprint"])
            if fp_counts:
                majority_fp, majority_n = fp_counts.most_common(1)[0]
                majority_candidates = [c for c in candidates if c["ast_fingerprint"] == majority_fp]
                majority_pick = max(majority_candidates, key=lambda c: c["raw_length"])
            else:
                majority_pick = longest_parsing
                majority_n = 1

            real_fallback_pick_key = None
            try:
                real_fallback_text = rd.select_best_fallback_candidate(opinions)
                for k, v in opinions.items():
                    if v == real_fallback_text:
                        real_fallback_pick_key = k
                        break
            except Exception:
                pass
            real_fallback_pick = next((c for c in candidates if c["key"] == real_fallback_pick_key), None)

            all_events.append({
                "task_id": r["task_id"], "arm": r["arm"], "stage": r["stage"],
                "historical_passed": r["passed"],
                "candidates": candidates,
                "event_classification": event_flags,
                "historical_synthesis": {
                    "parses": hist_synth_fp is not None,
                    "matches_any_candidate_ast": hist_synth_fp in [c["ast_fingerprint"] for c in candidates] if hist_synth_fp else False,
                },
                "selection_strategies": {
                    "real_select_best_fallback_candidate": {"key": real_fallback_pick_key, "correct": real_fallback_pick["passed"] if real_fallback_pick else None},
                    "longest_parsing": {"key": longest_parsing["key"], "correct": longest_parsing["passed"]},
                    "shortest_parsing": {"key": shortest_parsing["key"], "correct": shortest_parsing["passed"]},
                    "majority_structural_similarity": {"key": majority_pick["key"], "correct": majority_pick["passed"], "majority_size": majority_n},
                },
            })
            print(f"[{r['stage']}] {r['task_id']:8s} {r['arm']:14s} label={event_flags['label']:38s} "
                  f"n_correct={event_flags['n_correct']}/{event_flags['n_candidates']} "
                  f"real_fallback_correct={all_events[-1]['selection_strategies']['real_select_best_fallback_candidate']['correct']}")

    out_path = "/tmp/tier6_disagreement_analysis_raw.json"
    with open(out_path, "w") as f:
        json.dump(all_events, f, indent=2)
    print(f"\nFull raw data written to {out_path}")

    # ---- Summary stats ----
    for arm in ("ARCH_COUNCIL", "BASE_N"):
        events = [e for e in all_events if e["arm"] == arm]
        n = len(events)
        print(f"\n{'='*70}\n{arm} (n={n})\n{'='*70}")
        label_counts = Counter(e["event_classification"]["label"] for e in events)
        for label, count in label_counts.most_common():
            print(f"  {label:42s} {count:3d} ({100*count/n:.1f}%)")

        # Fallback heuristic precision, ONLY on events where a choice among
        # disagreeing candidates is actually meaningful (i.e. NOT
        # exact_agreement_all -- there's nothing to choose there) and NOT
        # all_incorrect (no correct option exists to possibly miss).
        disagreement_events = [
            e for e in events
            if e["event_classification"]["label"] not in ("exact_agreement_all_correct", "exact_agreement_all_incorrect")
            and e["event_classification"]["n_correct"] > 0
        ]
        print(f"\n  Events with real disagreement AND >=1 correct candidate available: {len(disagreement_events)}")
        for strategy in ["real_select_best_fallback_candidate", "longest_parsing", "shortest_parsing", "majority_structural_similarity"]:
            correct_picks = sum(1 for e in disagreement_events if e["selection_strategies"][strategy]["correct"])
            print(f"    {strategy:38s}: picks correct {correct_picks}/{len(disagreement_events)} "
                  f"({100*correct_picks/len(disagreement_events):.1f}%)" if disagreement_events else "n/a")

        # Correctness by length rank across ALL candidates (not just fallback events)
        all_candidates_flat = [(c, e) for e in events for c in e["candidates"]]
        # rank within each event by raw_length
        rank_correct = {0: [], 1: [], 2: []}  # 0=longest, 1=middle, 2=shortest
        for e in events:
            ranked = sorted(e["candidates"], key=lambda c: -c["raw_length"])
            for i, c in enumerate(ranked):
                if i < 3:
                    rank_correct[i].append(c["passed"])
        print("\n  Correctness by length rank (0=longest, 2=shortest), ALL events:")
        for rank, vals in rank_correct.items():
            if vals:
                print(f"    rank {rank}: {sum(vals)}/{len(vals)} ({100*sum(vals)/len(vals):.1f}%)")


if __name__ == "__main__":
    main()
