#!/usr/bin/env python3
"""
STRICTLY READ-ONLY verification of select_best_fallback_candidate()
(app/core/river_deliberation.py) against the real, already-captured
Tier-4 coding corpus (audits/tier4_apparatus/). Makes ZERO new LLM/model
calls and ZERO new sandbox executions -- reuses ground-truth correctness
already computed once, during the original Tier-6 forensic audit run
(cached at /tmp/tier6_disagreement_analysis_raw.json; falls back to
raising a clear error telling you to re-run
scripts/tier6_disagreement_analysis.py if that cache is gone, rather than
silently regenerating different numbers).

Built 2026-09-09 while implementing PENDING_DECISIONS.md #20. A first
implementation attempt (stage 3 = "prefer longest" for the no-majority
case, preserving this function's pre-existing tie-break) measured only
79.2%/88.0% against this corpus -- barely above, and on BASE_N slightly
below, the pre-fix baseline (78.2%/89.3%). Traced to root cause before
accepting that result: stage 1 (a genuine 2+ AST-fingerprint majority)
only fires in ~20% of real disagreement events; stage 3 dominates ~80% of
real outcomes, and "prefer longest" is exactly the behavior Tier-6's own
report found weakest (78.2%) versus "prefer shortest" (93.6%) on this
corpus. Flipped stage 3 to shortest; this script is what confirmed the
fix, not a claim taken on faith.
"""
import json
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, ".")

import app.core.river_deliberation as rd  # noqa: E402

TIER4_DIR = "audits/tier4_apparatus"
CACHE_PATH = "/tmp/tier6_disagreement_analysis_raw.json"


def load_stage_records(stage_num):
    with open(f"{TIER4_DIR}/stage{stage_num}_results.jsonl") as f:
        return [json.loads(l) for l in f]


def candidate_calls(record):
    if record["arm"] == "ARCH_COUNCIL":
        calls = record["mechanism_calls"][1:-1]
        return {c["model"]: c["response_text"] for c in calls}
    calls = record["mechanism_calls"][:-1]
    return {f"{c['model']}#{i}": c["response_text"] for i, c in enumerate(calls)}


def main():
    if not os.path.exists(CACHE_PATH):
        print(
            f"[verify] {CACHE_PATH} not found -- re-run "
            f"scripts/tier6_disagreement_analysis.py first to regenerate it "
            f"(that script performs real, read-only sandbox re-verification; "
            f"this script does not)."
        )
        sys.exit(1)

    with open(CACHE_PATH) as f:
        cached_events = json.load(f)

    records_by_key = {}
    for stage_num in (1, 2):
        for r in load_stage_records(stage_num):
            records_by_key[(r["task_id"], r["arm"], stage_num)] = r

    results = {
        "ARCH_COUNCIL": {"n": 0, "correct": 0},
        "BASE_N": {"n": 0, "correct": 0},
    }
    by_stage = {"stage1_majority": {"n": 0, "correct": 0}, "stage3_no_majority": {"n": 0, "correct": 0}}
    skipped = 0

    for e in cached_events:
        flags = e["event_classification"]
        if flags["exact_agreement_all"] or flags["all_incorrect"]:
            continue  # matches Tier-6's own inclusion criterion exactly

        k = (e["task_id"], e["arm"], e["stage"])
        record = records_by_key.get(k)
        if record is None:
            skipped += 1
            continue
        opinions = candidate_calls(record)
        cached_correctness = {c["key"]: c["passed"] for c in e["candidates"]}

        try:
            pick_text = rd.select_best_fallback_candidate(opinions)
        except Exception:
            skipped += 1
            continue

        pick_key = next((k2 for k2, v in opinions.items() if v == pick_text), None)
        if pick_key is None or pick_key not in cached_correctness:
            skipped += 1
            continue

        arm = e["arm"]
        correct = bool(cached_correctness[pick_key])
        results[arm]["n"] += 1
        results[arm]["correct"] += int(correct)

        stage_bucket = "stage1_majority" if flags["ast_agreement_count"] >= 2 else "stage3_no_majority"
        by_stage[stage_bucket]["n"] += 1
        by_stage[stage_bucket]["correct"] += int(correct)

    print("=== select_best_fallback_candidate() vs. real Tier-4 corpus ===")
    for arm, d in results.items():
        rate = d["correct"] / d["n"] if d["n"] else 0
        print(f"{arm}: {d['correct']}/{d['n']} correct ({rate:.1%})")
    print()
    for bucket, d in by_stage.items():
        rate = d["correct"] / d["n"] if d["n"] else 0
        print(f"{bucket}: {d['correct']}/{d['n']} correct ({rate:.1%})")
    print(f"\nskipped (unmatched/errored): {skipped}")


if __name__ == "__main__":
    main()
