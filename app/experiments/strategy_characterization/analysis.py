#!/usr/bin/env python3
"""Pre-registered Stage-1 analysis, per the CORRECTED, controlling frozen protocol
(audits/2026-09-27_strategy_characterization_protocol_design.md Section 7/8, as
corrected by the adversarial review). Read-only against log_stage1.jsonl -- makes no
model calls, writes no state back into the log.

Primary test: template-level (n=6) Friedman omnibus.
Secondary/exploratory: pooled n=18 Friedman + Bonferroni-corrected pairwise Wilcoxon
(both units), explicitly labeled non-confirmatory per the correction.
Q2: only `return_type` is eligible (dimensions.py); `operation`/`arg_count` reported,
if at all, as structurally-confounded, never as findings.
Q3: per-strategy and pooled flip-rate.
Q4: naive + split-sample-corrected oracle ceiling, at both units.
"""
from __future__ import annotations
import sys
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scipy import stats  # noqa: E402

from .common import EXP_ROOT, STRATEGIES, K_REPEATS, read_jsonl  # noqa: E402
from .dimensions import TASK_DIMENSIONS, DIMENSION_ELIGIBLE  # noqa: E402

TASK_IDS = sorted(TASK_DIMENSIONS.keys())  # K2.T1..K2.T6, fixed, exhaustive


def load_rows():
    return read_jsonl(EXP_ROOT / "stage1" / "log_stage1.jsonl")


def cell_pass_rate(rows, task_id, world, strategy, rep_slice=None):
    """Mean pass rate for one (task, world, strategy) cell, optionally restricted to a
    slice of repeat indices (used by the Q4 split-sample correction)."""
    cell = [r for r in rows if r["task_id"] == task_id and r["world_index"] == world and r["strategy"] == strategy]
    if rep_slice is not None:
        cell = [r for r in cell if r["repeat_index"] in rep_slice]
    if not cell:
        return None
    return mean(1.0 if r["passed"] else 0.0 for r in cell)


def template_matrix(rows, worlds, rep_slice=None):
    """{task_id: {strategy: mean_pass_rate averaged across all worlds}} -- the n=6
    PRIMARY unit. Each task's rate is the mean over its (up to) N_WORLDS x K_REPEATS
    real observations."""
    out = {}
    for task_id in TASK_IDS:
        out[task_id] = {}
        for strategy in STRATEGIES:
            rates = [cell_pass_rate(rows, task_id, w, strategy, rep_slice) for w in worlds]
            rates = [r for r in rates if r is not None]
            out[task_id][strategy] = mean(rates) if rates else None
    return out


def pooled_matrix(rows, worlds, rep_slice=None):
    """{(task_id, world): {strategy: mean_pass_rate}} -- the n=18 SECONDARY/EXPLORATORY
    unit (anti-conservative: treats worlds as fresh independent templates)."""
    out = {}
    for task_id in TASK_IDS:
        for w in worlds:
            key = (task_id, w)
            out[key] = {s: cell_pass_rate(rows, task_id, w, s, rep_slice) for s in STRATEGIES}
    return out


def _friedman(matrix_values):
    """matrix_values: list of [v_DIRECT, v_STEPWISE, v_WORKED_EXAMPLE] rows (blocks).
    Returns scipy FriedmanchisquareResult, or None if any column is constant/degenerate
    (scipy raises on fully-tied data)."""
    cols = list(zip(*matrix_values))
    try:
        return stats.friedmanchisquare(*cols)
    except Exception as e:
        return f"friedman_error: {e}"


def _wilcoxon_pairs(matrix_values):
    """Returns {(sA,sB): scipy WilcoxonResult-or-error} for the 3 pairwise comparisons."""
    out = {}
    idx = {s: i for i, s in enumerate(STRATEGIES)}
    pairs = [("DIRECT", "STEPWISE"), ("DIRECT", "WORKED_EXAMPLE"), ("STEPWISE", "WORKED_EXAMPLE")]
    for a, b in pairs:
        xa = [row[idx[a]] for row in matrix_values]
        xb = [row[idx[b]] for row in matrix_values]
        diffs = [x - y for x, y in zip(xa, xb)]
        if all(d == 0 for d in diffs):
            out[(a, b)] = "all_differences_zero"
            continue
        try:
            out[(a, b)] = stats.wilcoxon(xa, xb)
        except Exception as e:
            out[(a, b)] = f"wilcoxon_error: {e}"
    return out


def q1_analysis(rows, worlds):
    tmpl = template_matrix(rows, worlds)
    tmpl_rows = [[tmpl[t][s] for s in STRATEGIES] for t in TASK_IDS]
    friedman_n6 = _friedman(tmpl_rows)
    wilcoxon_n6 = _wilcoxon_pairs(tmpl_rows)

    pooled = pooled_matrix(rows, worlds)
    pooled_keys = sorted(pooled.keys())
    pooled_rows = [[pooled[k][s] for s in STRATEGIES] for k in pooled_keys]
    friedman_n18 = _friedman(pooled_rows)
    wilcoxon_n18 = _wilcoxon_pairs(pooled_rows)

    return {
        "template_matrix_n6": tmpl,
        "friedman_n6_PRIMARY": _fmt_friedman(friedman_n6),
        "wilcoxon_n6_EXPLORATORY_cannot_reach_corrected_alpha": _fmt_wilcoxon_dict(wilcoxon_n6),
        "pooled_matrix_n18": {f"{k[0]}|w{k[1]}": v for k, v in pooled.items()},
        "friedman_n18_SECONDARY_anticonservative": _fmt_friedman(friedman_n18),
        "wilcoxon_n18_EXPLORATORY_anticonservative": _fmt_wilcoxon_dict(wilcoxon_n18),
        "bonferroni_alpha": 0.05 / 3,
    }


def _fmt_friedman(res):
    if isinstance(res, str):
        return {"error": res}
    return {"statistic": res.statistic, "pvalue": res.pvalue}


def _fmt_wilcoxon_dict(d):
    out = {}
    for k, v in d.items():
        key = f"{k[0]}_vs_{k[1]}"
        if isinstance(v, str):
            out[key] = {"error": v}
        else:
            out[key] = {"statistic": v.statistic, "pvalue": v.pvalue}
    return out


def q2_analysis(rows, worlds):
    """Only `return_type` is eligible (dimensions.DIMENSION_ELIGIBLE). Reports the
    per-level mean pass rate per strategy at the template level (n=6, grouped by
    return_type) -- explicitly exploratory/hypothesis-generating only, per the
    corrected protocol; never a confirmatory claim on its own."""
    tmpl = template_matrix(rows, worlds)
    result = {"eligible_dimensions": [d for d, ok in DIMENSION_ELIGIBLE.items() if ok],
              "structurally_confounded_dimensions_NOT_TESTABLE": [d for d, ok in DIMENSION_ELIGIBLE.items() if not ok]}
    for dim, eligible in DIMENSION_ELIGIBLE.items():
        levels = {}
        for task_id in TASK_IDS:
            level = TASK_DIMENSIONS[task_id][dim]
            levels.setdefault(level, []).append(task_id)
        per_level = {}
        for level, task_ids_in_level in levels.items():
            per_level[str(level)] = {
                "n_tasks": len(task_ids_in_level),
                "task_ids": task_ids_in_level,
                "mean_pass_rate_per_strategy": {
                    s: mean(tmpl[t][s] for t in task_ids_in_level if tmpl[t][s] is not None)
                    for s in STRATEGIES
                },
            }
        result[dim] = {"eligible": eligible, "levels": per_level}
    return result


def q3_analysis(rows, worlds):
    """Flip-rate per strategy and pooled -- fraction of same-cell repeat PAIRS that
    disagree (pass vs fail), purely from re-sampling at temperature 0.2."""
    def flip_rate_for(strategy_filter):
        disagreements, total_pairs = 0, 0
        for task_id in TASK_IDS:
            for w in worlds:
                cell = [r for r in rows if r["task_id"] == task_id and r["world_index"] == w
                        and (strategy_filter is None or r["strategy"] == strategy_filter)]
                if strategy_filter is None:
                    # pooled: compute within each strategy separately, then aggregate
                    for s in STRATEGIES:
                        sub = [r for r in cell if r["strategy"] == s]
                        outcomes = [r["passed"] for r in sub]
                        for i in range(len(outcomes)):
                            for j in range(i + 1, len(outcomes)):
                                total_pairs += 1
                                if outcomes[i] != outcomes[j]:
                                    disagreements += 1
                else:
                    outcomes = [r["passed"] for r in cell]
                    for i in range(len(outcomes)):
                        for j in range(i + 1, len(outcomes)):
                            total_pairs += 1
                            if outcomes[i] != outcomes[j]:
                                disagreements += 1
        return {"disagreements": disagreements, "total_pairs": total_pairs,
                "flip_rate": (disagreements / total_pairs) if total_pairs else None}

    return {
        "pooled_all_strategies": flip_rate_for(None),
        "per_strategy": {s: flip_rate_for(s) for s in STRATEGIES},
    }


def q4_analysis(rows, worlds):
    """Naive (in-sample-inflated) and split-sample-corrected oracle ceiling, at both
    the n=6 template level and n=18 pooled level, per the corrected protocol."""
    def naive_ceiling(matrix, keys):
        deltas = []
        for k in keys:
            rates = matrix[k]
            vals = [v for v in rates.values() if v is not None]
            if not vals or rates.get("DIRECT") is None:
                continue
            deltas.append(max(vals) - rates["DIRECT"])
        return mean(deltas) if deltas else None

    def split_corrected_ceiling(worlds_):
        """Repeats 0-1 (first half of k=4) select; repeats 2-3 validate -- per task
        (template level, n=6), matching the frozen protocol's split-sample design."""
        deltas = []
        for task_id in TASK_IDS:
            select_rate_per_strategy = {}
            validate_rate_per_strategy = {}
            for s in STRATEGIES:
                sel = [cell_pass_rate(rows, task_id, w, s, rep_slice={0, 1}) for w in worlds_]
                val = [cell_pass_rate(rows, task_id, w, s, rep_slice={2, 3}) for w in worlds_]
                sel = [x for x in sel if x is not None]
                val = [x for x in val if x is not None]
                select_rate_per_strategy[s] = mean(sel) if sel else None
                validate_rate_per_strategy[s] = mean(val) if val else None
            if select_rate_per_strategy.get("DIRECT") is None:
                continue
            chosen = max((s for s in STRATEGIES if select_rate_per_strategy[s] is not None),
                         key=lambda s: select_rate_per_strategy[s])
            if validate_rate_per_strategy.get(chosen) is None or validate_rate_per_strategy.get("DIRECT") is None:
                continue
            deltas.append(validate_rate_per_strategy[chosen] - validate_rate_per_strategy["DIRECT"])
        return mean(deltas) if deltas else None

    tmpl = template_matrix(rows, worlds)
    pooled = pooled_matrix(rows, worlds)

    return {
        "naive_ceiling_n6_template": naive_ceiling(tmpl, TASK_IDS),
        "naive_ceiling_n18_pooled": naive_ceiling(pooled, list(pooled.keys())),
        "split_sample_corrected_ceiling_n6_template": split_corrected_ceiling(worlds),
        "note": "Naive ceilings are definitionally inflated (selection bias). Split-sample "
                "correction removes bias but not selection-step noise (n=2 per side) -- read "
                "as a rough, exploratory bound, per the corrected protocol.",
    }


def run(worlds=(0, 1, 2)):
    rows = load_rows()
    n_expected = len(TASK_IDS) * len(worlds) * len(STRATEGIES) * K_REPEATS
    result = {
        "n_rows_logged": len(rows),
        "n_expected": n_expected,
        "complete": len(rows) == n_expected,
        "q1_global_strategy_effect": q1_analysis(rows, worlds),
        "q2_conditional_strategy_effect": q2_analysis(rows, worlds),
        "q3_within_strategy_noise": q3_analysis(rows, worlds),
        "q4_oracle_ceiling": q4_analysis(rows, worlds),
    }
    return result


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, default=str))
