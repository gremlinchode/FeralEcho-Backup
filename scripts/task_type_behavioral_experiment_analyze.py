#!/usr/bin/env python3
"""Final analysis pass for the task-type behavioral experiment.

This is the ONLY script in this experiment that reads condition_map_SEPARATE
.jsonl -- generation (task_type_behavioral_experiment.py) never saw it after
writing it, and judge scoring (task_type_behavioral_experiment_judge.py)
never opened it at all. This script joins trial_id -> condition only after
all responses are generated and all judge scores are computed, per the
mission's blinding requirement.
"""
import json
import re
import sys
from pathlib import Path

from scipy import stats

EVIDENCE_DIR = Path(sys.argv[1])
RAW_TRIALS_PATH = EVIDENCE_DIR / "raw_trials_anonymized.jsonl"
CONDITION_MAP_PATH = EVIDENCE_DIR / "condition_map_SEPARATE.jsonl"
JUDGE_SCORES_PATH = EVIDENCE_DIR / "judge_scores_anonymized.jsonl"
ANALYSIS_OUT_PATH = EVIDENCE_DIR / "analysis_result.json"

REAL_TURN5_RESPONSE = Path("/tmp/real_turn5_response.txt").read_text()


def has_list_structure(text: str) -> bool:
    numbered = len(re.findall(r"^\s*\d+[\.\)]\s", text, re.MULTILINE))
    bulleted = len(re.findall(r"^\s*[-*]\s", text, re.MULTILINE))
    return (numbered >= 3) or (bulleted >= 3)


def has_code_proxy(text: str) -> bool:
    """Same stated-crude-proxy definition as the archaeology note's §8, for
    direct comparability: fenced code block, or a line starting with
    def/class/import/from...import."""
    if "```" in text:
        return True
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("def ", "class ", "import ", "from ")) and (" import " in s or s.startswith(("import ", "def ", "class "))):
            return True
    return False


def jaccard_word_overlap(a: str, b: str) -> float:
    wa = set(re.findall(r"[a-z']+", a.lower()))
    wb = set(re.findall(r"[a-z']+", b.lower()))
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def main():
    trials = {}
    with open(RAW_TRIALS_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                t = json.loads(line)
                trials[t["trial_id"]] = t

    conditions = {}
    with open(CONDITION_MAP_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                c = json.loads(line)
                conditions[c["trial_id"]] = c

    judge_scores = {}
    with open(JUDGE_SCORES_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                j = json.loads(line)
                judge_scores[j["trial_id"]] = j

    print(f"trials={len(trials)} conditions={len(conditions)} judge_scores={len(judge_scores)}")

    rows = []
    missing_judge = []
    for trial_id, t in trials.items():
        cond = conditions.get(trial_id, {})
        judge = judge_scores.get(trial_id)
        if judge is None or not judge.get("parse_ok"):
            missing_judge.append(trial_id)
            continue
        resp = t["response"]
        rows.append({
            "trial_id": trial_id,
            "condition": cond.get("condition"),
            "task_type": cond.get("task_type"),
            "phase": t.get("phase"),
            "elapsed_s": t.get("elapsed_s"),
            "response_len": len(resp),
            "has_list": has_list_structure(resp),
            "has_code": has_code_proxy(resp),
            "jaccard_vs_real_turn5": jaccard_word_overlap(resp, REAL_TURN5_RESPONSE),
            "specificity": judge["specificity"],
            "relevance": judge["relevance"],
        })

    print(f"usable rows: {len(rows)}  missing/unparseable judge scores: {len(missing_judge)}")
    if missing_judge:
        print("  missing trial_ids:", [m[:8] for m in missing_judge])

    by_cond = {"A": [], "B": [], "C": []}
    for r in rows:
        if r["condition"] in by_cond:
            by_cond[r["condition"]].append(r)

    summary = {}
    for cond, rs in by_cond.items():
        if not rs:
            summary[cond] = {"n": 0}
            continue
        spec = [r["specificity"] for r in rs]
        rel = [r["relevance"] for r in rs]
        summary[cond] = {
            "n": len(rs),
            "specificity_mean": sum(spec) / len(spec),
            "specificity_median": sorted(spec)[len(spec) // 2],
            "specificity_values": spec,
            "relevance_mean": sum(rel) / len(rel),
            "relevance_values": rel,
            "response_len_mean": sum(r["response_len"] for r in rs) / len(rs),
            "has_list_rate": sum(r["has_list"] for r in rs) / len(rs),
            "has_code_rate": sum(r["has_code"] for r in rs) / len(rs),
            "jaccard_vs_real_turn5_mean": sum(r["jaccard_vs_real_turn5"] for r in rs) / len(rs),
        }

    print("\n=== PER-CONDITION SUMMARY ===")
    for cond in ["A", "B", "C"]:
        print(f"  {cond}: {json.dumps(summary[cond], indent=2)}")

    # Primary comparison: C vs B (specificity, Mann-Whitney U, unpaired --
    # trials are independent draws per condition, not seed-paired across
    # conditions, so an unpaired ordinal test is the methodologically
    # correct choice, not a paired test)
    result = {"summary": summary, "rows": rows, "missing_judge_count": len(missing_judge)}
    if summary["C"]["n"] >= 2 and summary["B"]["n"] >= 2:
        u_stat, p_cb = stats.mannwhitneyu(
            summary["C"]["specificity_values"], summary["B"]["specificity_values"],
            alternative="two-sided",
        )
        n1, n2 = summary["C"]["n"], summary["B"]["n"]
        rank_biserial_cb = 1 - (2 * u_stat) / (n1 * n2)
        result["primary_test_C_vs_B_specificity"] = {
            "test": "Mann-Whitney U (two-sided, unpaired)",
            "U": float(u_stat), "p_value": float(p_cb),
            "n_C": n1, "n_B": n2,
            "rank_biserial_effect_size": float(rank_biserial_cb),
            "median_C": summary["C"]["specificity_median"],
            "median_B": summary["B"]["specificity_median"] if summary["B"]["n"] else None,
        }
        print(f"\n=== PRIMARY TEST: C (coding/council) vs B (personal/council) specificity ===")
        print(json.dumps(result["primary_test_C_vs_B_specificity"], indent=2))

    if summary["B"]["n"] >= 2 and summary["A"]["n"] >= 2:
        u_stat2, p_ba = stats.mannwhitneyu(
            summary["B"]["specificity_values"], summary["A"]["specificity_values"],
            alternative="two-sided",
        )
        n1b, n2b = summary["B"]["n"], summary["A"]["n"]
        rank_biserial_ba = 1 - (2 * u_stat2) / (n1b * n2b)
        result["secondary_test_B_vs_A_specificity"] = {
            "test": "Mann-Whitney U (two-sided, unpaired)",
            "U": float(u_stat2), "p_value": float(p_ba),
            "n_B": n1b, "n_A": n2b,
            "rank_biserial_effect_size": float(rank_biserial_ba),
        }
        print(f"\n=== SECONDARY TEST: B (personal/council) vs A (personal/direct) specificity ===")
        print(json.dumps(result["secondary_test_B_vs_A_specificity"], indent=2))

    # Relevance, same comparisons, secondary endpoint
    if summary["C"]["n"] >= 2 and summary["B"]["n"] >= 2:
        u3, p3 = stats.mannwhitneyu(summary["C"]["relevance_values"], summary["B"]["relevance_values"], alternative="two-sided")
        result["secondary_test_C_vs_B_relevance"] = {"test": "Mann-Whitney U", "U": float(u3), "p_value": float(p3)}
        print("\n=== SECONDARY (relevance) C vs B ===")
        print(json.dumps(result["secondary_test_C_vs_B_relevance"], indent=2))

    ANALYSIS_OUT_PATH.write_text(json.dumps(result, indent=2, default=str))
    print(f"\nWritten: {ANALYSIS_OUT_PATH}")


if __name__ == "__main__":
    main()
