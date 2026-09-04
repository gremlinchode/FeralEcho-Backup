#!/usr/bin/env python3
"""Tier-4 confirmatory statistical analysis. Read-only against
audits/tier4_apparatus/stage{1,2}_results.jsonl. Implements exactly the
methodology frozen in audits/tier4_confirmatory_protocol.md: exact
two-sided McNemar test via direct binomial coefficient summation, Wilson
score CI, per-stage and pooled paired comparisons. Can be run after Stage
1 alone (interim analysis) or after both stages (pooled/final analysis).
"""
import json
import math
import sys
from itertools import combinations


def load_stage(stage_num: int) -> dict:
    path = f"audits/tier4_apparatus/stage{stage_num}_results.jsonl"
    records = []
    try:
        with open(path) as f:
            for line in f:
                records.append(json.loads(line))
    except FileNotFoundError:
        return {}
    by_task_arm = {}
    for r in records:
        by_task_arm[(r["task_id"], r["arm"])] = r
    return by_task_arm


def build_matrix(by_task_arm: dict) -> dict:
    """task_id -> {arm: passed_bool}"""
    tasks = sorted(set(k[0] for k in by_task_arm))
    matrix = {}
    for tid in tasks:
        matrix[tid] = {}
        for arm in ["BASE_1", "BASE_N", "ARCH_PIPELINE_ISOLATED", "ARCH_COUNCIL"]:
            rec = by_task_arm.get((tid, arm))
            matrix[tid][arm] = bool(rec.get("passed")) if rec else None
    return matrix


def exact_mcnemar_p(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value via binomial coefficient summation.
    b, c = discordant pair counts in each direction. n = b + c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    # P(X <= k) under Binomial(n, 0.5), doubled for two-sided, capped at 1.0
    def binom_pmf(i, n):
        return math.comb(n, i) / (2 ** n)
    cum = sum(binom_pmf(i, n) for i in range(0, k + 1))
    p = min(1.0, 2 * cum)
    return p


def wilson_ci(successes: int, total: int, z: float = 1.959964) -> tuple:
    if total == 0:
        return (0.0, 0.0)
    p_hat = successes / total
    denom = 1 + z**2 / total
    center = (p_hat + z**2 / (2 * total)) / denom
    half = (z * math.sqrt((p_hat * (1 - p_hat) / total) + (z**2 / (4 * total**2)))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def paired_compare(matrix: dict, arm_a: str, arm_b: str) -> dict:
    n = 0
    a_pass = b_pass = 0
    both_pass = both_fail = 0
    a_only = []  # tasks where a passed, b failed
    b_only = []  # tasks where b passed, a failed
    for tid, outcomes in matrix.items():
        pa, pb = outcomes[arm_a], outcomes[arm_b]
        if pa is None or pb is None:
            continue
        n += 1
        a_pass += int(pa)
        b_pass += int(pb)
        if pa and pb:
            both_pass += 1
        elif not pa and not pb:
            both_fail += 1
        elif pa and not pb:
            a_only.append(tid)
        else:
            b_only.append(tid)
    b_disc = len(a_only)  # a wins, b loses
    c_disc = len(b_only)  # b wins, a loses
    p = exact_mcnemar_p(b_disc, c_disc)
    return {
        "arm_a": arm_a, "arm_b": arm_b, "n": n,
        "rate_a": round(a_pass / n, 4) if n else None,
        "rate_b": round(b_pass / n, 4) if n else None,
        "absolute_diff_pp": round(100 * (b_pass - a_pass) / n, 2) if n else None,
        "both_pass": both_pass, "both_fail": both_fail,
        "a_only_wins": a_only, "b_only_wins": b_only,
        "discordant_favor_a": b_disc, "discordant_favor_b": c_disc,
        "exact_mcnemar_two_sided_p": round(p, 4),
    }


def summarize_arm(matrix: dict, arm: str) -> dict:
    outcomes = [v[arm] for v in matrix.values() if v[arm] is not None]
    n = len(outcomes)
    passed = sum(outcomes)
    ci = wilson_ci(passed, n) if n else (0.0, 0.0)
    return {"arm": arm, "n": n, "passed": passed,
            "rate": round(passed / n, 4) if n else None,
            "wilson_95ci": [round(ci[0], 4), round(ci[1], 4)]}


def failure_mode_breakdown(by_task_arm: dict, arm: str) -> dict:
    counts = {"PASS": 0, "TASK_LOGIC_FAILURE": 0, "GENERATION_TRUNCATED": 0, "INFRASTRUCTURE_FAILURE": 0}
    total = 0
    for (tid, a), rec in by_task_arm.items():
        if a != arm:
            continue
        total += 1
        c = rec.get("classification", "UNKNOWN")
        counts[c] = counts.get(c, 0) + 1
    counts["_total"] = total
    return counts


def run_analysis(stages: list):
    print(f"{'='*70}\nTIER-4 ANALYSIS -- stages: {stages}\n{'='*70}")
    combined_by_task_arm = {}
    per_stage_matrices = {}
    for s in stages:
        by_task_arm = load_stage(s)
        if not by_task_arm:
            print(f"[stage {s}] NO RESULTS YET")
            continue
        matrix = build_matrix(by_task_arm)
        per_stage_matrices[s] = matrix
        print(f"\n--- STAGE {s} (n={len(matrix)} tasks) ---")
        for arm in ["BASE_1", "BASE_N", "ARCH_PIPELINE_ISOLATED", "ARCH_COUNCIL"]:
            summary = summarize_arm(matrix, arm)
            fm = failure_mode_breakdown(by_task_arm, arm)
            print(f"  {arm:24s} {summary['passed']:3d}/{summary['n']:3d} "
                  f"= {summary['rate']*100:.1f}%  CI={summary['wilson_95ci']}  {fm}")
        print(f"\n  PRIMARY (Stage {s} only): BASE_N vs ARCH_COUNCIL")
        cmp = paired_compare(matrix, "BASE_N", "ARCH_COUNCIL")
        print(f"    {json.dumps(cmp, indent=4)}")
        print(f"\n  SECONDARY (Stage {s} only):")
        for a, b in [("BASE_1", "BASE_N"), ("BASE_1", "ARCH_PIPELINE_ISOLATED"), ("BASE_1", "ARCH_COUNCIL")]:
            cmp = paired_compare(matrix, a, b)
            print(f"    {a} vs {b}: rate_a={cmp['rate_a']} rate_b={cmp['rate_b']} "
                  f"diff_pp={cmp['absolute_diff_pp']} disc=({cmp['discordant_favor_a']},{cmp['discordant_favor_b']}) "
                  f"p={cmp['exact_mcnemar_two_sided_p']}")
        for k, v in by_task_arm.items():
            combined_by_task_arm[(f"s{s}_{k[0]}", k[1])] = v

    if len(per_stage_matrices) >= 2:
        print(f"\n{'='*70}\nPOOLED ACROSS STAGES {list(per_stage_matrices.keys())}\n{'='*70}")
        pooled_matrix = build_matrix(combined_by_task_arm)
        for arm in ["BASE_1", "BASE_N", "ARCH_PIPELINE_ISOLATED", "ARCH_COUNCIL"]:
            summary = summarize_arm(pooled_matrix, arm)
            print(f"  {arm:24s} {summary['passed']:3d}/{summary['n']:3d} "
                  f"= {summary['rate']*100:.1f}%  CI={summary['wilson_95ci']}")
        print("\n  PRIMARY (POOLED): BASE_N vs ARCH_COUNCIL")
        cmp = paired_compare(pooled_matrix, "BASE_N", "ARCH_COUNCIL")
        print(f"    {json.dumps(cmp, indent=4)}")
        print("\n  SECONDARY (POOLED):")
        for a, b in [("BASE_1", "BASE_N"), ("BASE_1", "ARCH_PIPELINE_ISOLATED"), ("BASE_1", "ARCH_COUNCIL")]:
            cmp = paired_compare(pooled_matrix, a, b)
            print(f"    {a} vs {b}: rate_a={cmp['rate_a']} rate_b={cmp['rate_b']} "
                  f"diff_pp={cmp['absolute_diff_pp']} disc=({cmp['discordant_favor_a']},{cmp['discordant_favor_b']}) "
                  f"p={cmp['exact_mcnemar_two_sided_p']}")

    return per_stage_matrices


if __name__ == "__main__":
    stages_arg = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [1, 2]
    run_analysis(stages_arg)
