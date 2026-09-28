"""Stage 0 GRADER / ANALYSIS. Re-derives every prompt from the frozen plan, re-executes every stored response against the hidden tests
(twice, with fresh nonces), computes the pre-registered metrics and the verdict. Runs OUTSIDE the arm jails (it reads the oracle).
usage: python -I -B grade.py [--tag primary]"""
import argparse, math, random, statistics, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import common, prompts, ollama_client, oracle_runner, worlds, tasks
from app.experiments.accumulation_probe.common import EXP_ROOT, ARMS, read_json, read_jsonl, sha256_obj

S0 = EXP_ROOT / "stage0"
# ---- PRE-REGISTERED DECISION CONSTANTS (v1) ----
HEADROOM_MIN = 0.30          # H - N and H - NEUTRAL (pooled T+S), point estimate
HEADROOM_LOWER_MIN = 0.15    # one-sided 95% cluster-bootstrap lower bound of each of the two contrasts
PER_CONV_HEADROOM = 0.30     # H - N per convention, required in >= 2 of 3 conventions
N_CEILING = 0.40             # N pooled T+S pass rate must not exceed this (headroom exists)
NOISE_MAX = 0.10             # |rate(N)-rate(N2)| and |rate(H)-rate(H2)| pooled T+S
MISMATCH_GAP_MIN = 0.20      # H - MISMATCH (content-conditioning check)
REGRADE_AGREE_MIN = 0.99; INFRA_MAX = 0.02; TRUNC_MAX = 0.05
BOOT_N = 10000

def mean(x): x = list(x); return sum(x) / len(x) if x else float("nan")
def boot(a, b=None, seed=12345):
    ids = sorted(a); rng = random.Random(seed); st = []
    for _ in range(BOOT_N):
        s = [rng.choice(ids) for _ in ids]
        st.append(mean(a[i] - (b[i] if b else 0) for i in s))
    st.sort(); pt = mean(a[i] - (b[i] if b else 0) for i in ids)
    return {"point": round(pt, 4), "ci95": [round(st[int(.025 * BOOT_N)], 4), round(st[int(.975 * BOOT_N)], 4)], "lower95_one_sided": round(st[int(.05 * BOOT_N)], 4), "n_tasks": len(ids)}

def load():
    f = read_json(S0 / "FREEZE.json"); meta = {t["task_id"]: t for t in read_json(S0 / "oracle" / "task_meta.json")}
    tests = read_json(S0 / "oracle" / "hidden_tests.json"); W = read_json(S0 / "oracle" / "worlds.json")
    pub = {t["task_id"]: t for t in read_json(S0 / "public" / "public_tasks.json")}
    plans = {a: read_json(S0 / "runs" / a / "plan.json") for a in ARMS}; rows = {a: read_jsonl(S0 / "runs" / a / "calls.jsonl") for a in ARMS}
    return f, meta, tests, W, pub, plans, rows

def check_chain(rows):
    """Each arm ledger is a hash chain (prev_sha256): detects edited, deleted, reordered or substituted rows."""
    v = []
    for arm in ARMS:
        prev = "GENESIS"
        for i, r in enumerate(rows[arm]):
            if r.get("prev_sha256") != prev: v.append(f"{arm}: chain broken at row {i} ({r.get('call_id')})"); break
            prev = common.sha256_obj(r)
    return v

def check_requests(rows, plans, pub, meta, tests, W):
    """Contamination / integrity checks on the requests that were ACTUALLY sent (not the plan)."""
    v = []; true_tables = {"K1": tasks.k1_table(W["true"]["K1"]), "K2": tasks.k2_pri(W["true"]["K2"]), "K3": tasks.k3_table(W["true"]["K3"])}
    toks = {k: worlds.tokens(W["true"][k]) for k in W["true"]}
    lit = [(tid, repr(tuple(c["args"]))) for tid, t in tests.items() for c in t["cases"] if len(repr(tuple(c["args"]))) > 25]
    n = 0
    for arm in ARMS:
        planmap = {c["call_id"]: c for c in plans[arm]["calls"]}
        for r in rows[arm]:
            if "response_text" not in r: continue
            n += 1; c = planmap[r["call_id"]]; sysm, usr = prompts.build_messages(pub[c["task_id"]], c["carrier_block"], c["inline_examples"])
            body = ollama_client.request_body(plans[arm]["model"], sysm, usr, c["seed"], plans[arm]["options"])
            if common.sha256_obj(body) != r["request_sha256"]: v.append(f"{r['call_id']}: sent request differs from the frozen plan")
            text = r["request"]["messages"][0]["content"] + "\n" + r["request"]["messages"][1]["content"]; t = meta[r["task_id"]]
            if any(l in text for tid, l in lit): v.append(f"{r['call_id']}: hidden-test literal present in request")
            if arm in ("N", "N2") and (prompts.BLOCK_OPEN in text or "Examples observed" in text): v.append(f"{r['call_id']}: carrier content in N request")
            if arm in ("N", "N2", "NEUTRAL") and t["split"] != "NEAR" and any(x in text for k in toks for x in toks[k]): v.append(f"{r['call_id']}: true-world token in {arm} request")
            if arm in ("NEUTRAL", "MISMATCH") and any(tt in text for tt in true_tables.values()): v.append(f"{r['call_id']}: true table present in {arm} request")
            if r["request"]["options"]["seed"] != c["seed"]: v.append(f"{r['call_id']}: seed mismatch")
    v += check_chain(rows)
    return {"requests_checked": n, "violations": v, "ok": not v}

def grade_all(rows, meta, tests):
    out = []
    for arm in ARMS:
        for r in rows[arm]:
            if "response_text" not in r: continue
            code = oracle_runner.extract_code(r["response_text"], tests[r["task_id"]]["fn"]); test = tests[r["task_id"]]["test_code"]
            if code:
                g1 = oracle_runner.grade(code, test); k = 0
                while g1["infra"] and k < 2: g1 = oracle_runner.grade(code, test); k += 1
                g2 = oracle_runner.grade(code, test)
            else:
                g1 = g2 = {"passed": False, "infra": False, "ran_ok": False, "duration": 0.0, "timeout": False, "output_tail": "", "error_tail": "no code extracted"}
            out.append({"call_id": r["call_id"], "arm": arm, "task_id": r["task_id"], "variant": r["variant"], "replicate": r["replicate"], "sample": r["sample"], "probe": r["probe"],
                        "passed": g1["passed"], "regrade_passed": g2["passed"], "infra": g1["infra"], "timeout": g1.get("timeout", False), "no_code": not code,
                        "truncated": r.get("done_reason") == "length", "code_sha256": common.sha256_text(code), "response_sha256": r["response_sha256"],
                        "eval_count": r.get("eval_count"), "wall_s": r.get("wall_s"), "error_tail": g1["error_tail"][-160:]})
    return out

def units(grades, arm, splits, meta, variant_ok=lambda v: v == "-"):
    d = {}
    for g in grades:
        if g["arm"] == arm and not g["probe"] and meta[g["task_id"]]["split"] in splits and variant_ok(g["variant"]):
            d.setdefault((g["task_id"], g["variant"]), []).append(1.0 if g["passed"] else 0.0)
    return {k: mean(v) for k, v in d.items()}

def analyze(grades, rows, plans, meta, tests, W, f, req):
    TS = ("T", "S"); R = {}
    U = {a: units(grades, a, TS, meta) for a in ARMS}
    U = {a: {k[0]: v for k, v in u.items()} for a, u in U.items()}
    R["pass_rates_T_S"] = {a: round(mean(U[a].values()), 4) for a in ARMS}
    R["pass_rates_by_split"] = {a: {s: round(mean(units(grades, a, (s,), meta, variant_ok=lambda v: True).values()), 4) if units(grades, a, (s,), meta, variant_ok=lambda v: True) else None for s in ("T", "S", "NEAR", "UNREL")} for a in ARMS}
    R["by_convention_T_S"] = {a: {k: round(mean(v for t, v in U[a].items() if meta[t]["kind"] == k), 4) for k in ("K1", "K2", "K3")} for a in ARMS}
    R["by_template_H_vs_N"] = {t: {"N": round(U["N"][t], 3), "NEUTRAL": round(U["NEUTRAL"][t], 3), "MISMATCH": round(U["MISMATCH"][t], 3), "H": round(U["H"][t], 3), "E": round(U["E"][t], 3), "IC": round(U["IC"][t], 3)} for t in sorted(U["N"])}
    C = {}
    for name, (a, b) in {"H-N": ("H", "N"), "H-NEUTRAL": ("H", "NEUTRAL"), "H-MISMATCH": ("H", "MISMATCH"), "IC-N": ("IC", "N"), "E-N": ("E", "N"), "NEUTRAL-N": ("NEUTRAL", "N"), "MISMATCH-N": ("MISMATCH", "N"),
                         "H-IC": ("H", "IC"), "H-E": ("H", "E"), "N-N2 (noise)": ("N", "N2"), "H-H2 (noise)": ("H", "H2")}.items():
        common_t = sorted(set(U[a]) & set(U[b])); C[name] = boot({t: U[a][t] for t in common_t}, {t: U[b][t] for t in common_t})
    R["contrasts_T_S"] = C
    R["headroom_per_convention_H_minus_N"] = {k: round(mean(U["H"][t] - U["N"][t] for t in U["H"] if meta[t]["kind"] == k), 4) for k in ("K1", "K2", "K3")}
    # noise floor + seed variance
    nd = [U["N"][t] - U["N2"][t] for t in U["N"]]; hd = [U["H"][t] - U["H2"][t] for t in U["H"]]
    R["noise_floor"] = {"N_vs_N2": {"pooled_rate_diff": round(mean(nd), 4), "mean_abs_task_diff": round(mean(abs(x) for x in nd), 4), "sd_task_diff": round(statistics.pstdev(nd), 4)},
                        "H_vs_H2": {"pooled_rate_diff": round(mean(hd), 4), "mean_abs_task_diff": round(mean(abs(x) for x in hd), 4), "sd_task_diff": round(statistics.pstdev(hd), 4)}}
    sv = {}
    for a in ARMS:
        by = {}
        for g in grades:
            if g["arm"] == a and not g["probe"] and meta[g["task_id"]]["split"] in TS: by.setdefault(g["task_id"], []).append(g)
        mixed = mean(1.0 if 0 < mean(1.0 if x["passed"] else 0.0 for x in v) < 1 else 0.0 for v in by.values())
        distinct = mean(1.0 if len({x["response_sha256"] for x in v}) > 1 else 0.0 for v in by.values())
        wsd = mean(statistics.pstdev([1.0 if x["passed"] else 0.0 for x in v]) for v in by.values())
        sv[a] = {"frac_tasks_mixed_pass_fail_across_seeds": round(mixed, 3), "frac_tasks_with_differing_responses_across_seeds": round(distinct, 3), "mean_within_task_sd": round(wsd, 3)}
    R["seed_variance"] = sv
    tfv = {}
    for a in ("N", "H"):
        for k in ("K1", "K2", "K3"):
            tfv[f"{a}.{k}"] = round(statistics.pstdev([v for t, v in U[a].items() if meta[t]["kind"] == k]), 4)
        tfv[f"{a}.sd_across_all_tasks"] = round(statistics.pstdev(list(U[a].values())), 4)
    tfv["H.range_of_convention_means"] = round(max(R["by_convention_T_S"]["H"].values()) - min(R["by_convention_T_S"]["H"].values()), 4)
    R["task_family_variance"] = tfv
    # determinism probes
    byid = {g["call_id"]: g for g in grades}; det = []
    for g in grades:
        if g["probe"]: o = byid.get(g["call_id"].replace("|probe", "")); det.append(bool(o) and o["response_sha256"] == g["response_sha256"])
    R["determinism_probe"] = {"pairs": len(det), "identical_response_with_same_seed": sum(det)}
    # negative controls
    def nu(arm, split, variants): return {k: v for k, v in units(grades, arm, (split,), meta, variant_ok=lambda x: x in variants).items()}
    neg = {}
    for split, vmap in (("NEAR", {"N": ("-",), "NEUTRAL": ("-",), "H": ("-",)}), ("UNREL", {"N": ("-",), "NEUTRAL": ("K1neutral",), "H": ("K1", "K2", "K3")})):
        rates = {a: {"pass_rate": round(mean(nu(a, split, vs).values()), 4), "n_units": len(nu(a, split, vs))} for a, vs in vmap.items()}
        neg[split] = {**rates, "H_minus_N": round(rates["H"]["pass_rate"] - rates["N"]["pass_rate"], 4), "NEUTRAL_minus_N": round(rates["NEUTRAL"]["pass_rate"] - rates["N"]["pass_rate"], 4)}
    R["negative_controls"] = neg
    # oracle / instrument integrity
    q = read_json(S0 / "reports" / "oracle_qualification.json")
    real = [g for g in grades]; agree = mean(1.0 if g["passed"] == g["regrade_passed"] else 0.0 for g in real)
    R["oracle_agreement"] = {"independent_implementation_disagreements": q["ab_disagreements"], "mutants_total": q["mutants_total"], "mutants_survived": q["mutants_survived"], "spoof_passed": q["spoof_passed"],
                             "runtime_vs_regrade_agreement": round(agree, 4), "responses_graded": len(real)}
    R["integrity"] = {"infra_failure_rate": round(mean(1.0 if g["infra"] else 0.0 for g in real), 4), "truncation_rate": round(mean(1.0 if g["truncated"] else 0.0 for g in real), 4),
                      "no_code_rate": round(mean(1.0 if g["no_code"] else 0.0 for g in real), 4), "timeout_rate": round(mean(1.0 if g["timeout"] else 0.0 for g in real), 4),
                      "calls_planned": sum(len(p["calls"]) for p in plans.values()), "calls_completed": len(real), "request_checks": req}
    lat = [g["wall_s"] for g in real if g["wall_s"]]; R["latency_s"] = {"mean": round(mean(lat), 2), "median": round(statistics.median(lat), 2), "max": round(max(lat), 2), "mean_eval_tokens": round(mean(g["eval_count"] for g in real if g["eval_count"]), 1)}
    return R, U

def verdict(R, U, meta):
    C = R["contrasts_T_S"]; g = {}; why = []
    g["G1_headroom"] = all(C[k]["point"] >= HEADROOM_MIN and C[k]["lower95_one_sided"] >= HEADROOM_LOWER_MIN for k in ("H-N", "H-NEUTRAL"))
    if not g["G1_headroom"]: why.append(f"headroom: H-N={C['H-N']['point']} (lower95 {C['H-N']['lower95_one_sided']}), H-NEUTRAL={C['H-NEUTRAL']['point']} (lower95 {C['H-NEUTRAL']['lower95_one_sided']}); need >= {HEADROOM_MIN} with lower95 >= {HEADROOM_LOWER_MIN}")
    pc = R["headroom_per_convention_H_minus_N"]; g["G2_two_of_three_conventions"] = sum(1 for v in pc.values() if v >= PER_CONV_HEADROOM) >= 2
    if not g["G2_two_of_three_conventions"]: why.append(f"per-convention H-N {pc}: fewer than 2 of 3 reach {PER_CONV_HEADROOM}")
    g["G3_n_below_ceiling"] = R["pass_rates_T_S"]["N"] <= N_CEILING
    if not g["G3_n_below_ceiling"]: why.append(f"N pass rate {R['pass_rates_T_S']['N']} > {N_CEILING}")
    nf = R["noise_floor"]; g["G4_noise_floor"] = abs(nf["N_vs_N2"]["pooled_rate_diff"]) <= NOISE_MAX and abs(nf["H_vs_H2"]["pooled_rate_diff"]) <= NOISE_MAX
    if not g["G4_noise_floor"]: why.append(f"noise floor: N-N2 {nf['N_vs_N2']['pooled_rate_diff']}, H-H2 {nf['H_vs_H2']['pooled_rate_diff']} exceed {NOISE_MAX}")
    g["G5_content_conditioning_H_minus_MISMATCH"] = C["H-MISMATCH"]["point"] >= MISMATCH_GAP_MIN
    if not g["G5_content_conditioning_H_minus_MISMATCH"]: why.append(f"H-MISMATCH={C['H-MISMATCH']['point']} < {MISMATCH_GAP_MIN}")
    o = R["oracle_agreement"]; i = R["integrity"]
    g["G6_instrument_integrity"] = (o["independent_implementation_disagreements"] == 0 and o["mutants_survived"] == 0 and o["spoof_passed"] == 0 and o["runtime_vs_regrade_agreement"] >= REGRADE_AGREE_MIN
                                    and i["infra_failure_rate"] <= INFRA_MAX and i["truncation_rate"] <= TRUNC_MAX and i["request_checks"]["ok"] and i["calls_completed"] == i["calls_planned"])
    if not g["G6_instrument_integrity"]: why.append(f"instrument integrity failed: oracle={o}, integrity={ {k: v for k, v in i.items() if k != 'request_checks'} }, request_checks_ok={i['request_checks']['ok']}")
    ok = all(g.values())
    diag = None
    if not g["G1_headroom"]:
        diag = ("FORMAT-CONSUMPTION SUSPECTED: the same information works inline (IC-N >= 0.30) but not in the retained-carrier format" if C["IC-N"]["point"] >= 0.30
                else "WORKER/TASK/INSTRUMENT: even inline information (IC) does not lift performance; the failure is not specific to the carrier format")
    return {"gates": g, "verdict": "INFORMATIVE" if ok else "UNINFORMATIVE", "reasons_if_uninformative": why, "diagnostic_if_g1_fails": diag,
            "can_this_worker_use_this_carrier": ("YES" if (g["G1_headroom"] and g["G5_content_conditioning_H_minus_MISMATCH"]) else "NOT ESTABLISHED"),
            "note": "UNINFORMATIVE is an instrument/consumption outcome, not evidence against experience-based learning."}

def defensibility(R, U, meta):
    """Are the pre-registered Stage 1 thresholds (+25 transfer, +30 headroom, +-10 negatives) defensible given Stage 0's measured variability?"""
    z = 1.645 + 0.842; n = len(U["H"]); d = [U["H"][t] - U["N"][t] for t in U["H"]]; sd_eff = statistics.pstdev(d)
    mde = z * sd_eff / math.sqrt(n)
    out = {"n_tasks_pooled_T_S": n, "sd_task_level_H_minus_N": round(sd_eff, 4), "mde_80pct_power_alpha05_one_sided_pooled": round(mde, 4),
           "plus25_transfer_threshold_resolvable": mde <= 0.25, "plus30_headroom_margin_over_threshold": round(R["contrasts_T_S"]["H-N"]["point"] - HEADROOM_MIN, 4)}
    for split in ("NEAR", "UNREL"):
        res = R["negative_controls"][split]; nn = res["N"]["n_units"]
        sd = statistics.pstdev([0.0] + [abs(res["H_minus_N"])]) if nn <= 1 else None
        half = 1.645 * max(R["noise_floor"]["N_vs_N2"]["sd_task_diff"], R["noise_floor"]["H_vs_H2"]["sd_task_diff"]) / math.sqrt(max(nn, 1))
        out[f"minus_plus10_equivalence_halfwidth_{split}"] = {"n_task_units": nn, "approx_90pct_halfwidth_from_replicate_noise_only": round(half, 4), "resolvable_at_10pp": half <= 0.10}
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tag", default="primary"); a = ap.parse_args()
    out = S0 / "results" / a.tag
    if out.exists(): sys.exit(f"STOP: {out} exists; results are immutable (use a new --tag)")
    f, meta, tests, W, pub, plans, rows = load()
    req = check_requests(rows, plans, pub, meta, tests, W); grades = grade_all(rows, meta, tests)
    R, U = analyze(grades, rows, plans, meta, tests, W, f, req); V = verdict(R, U, meta); D = defensibility(R, U, meta)
    out.mkdir(parents=True)
    for g in grades: common.append_jsonl(out / "grades.jsonl", g)
    common.write_json_new(out / "metrics.json", {"frozen": {"preregistration_sha256": f["preregistration"]["sha256"], "git_head": f["git"]["head"], "model": f["model"]}, "metrics": R, "verdict": V, "threshold_defensibility": D})
    print(json_dump({"verdict": V, "rates": R["pass_rates_T_S"], "contrasts": {k: (v["point"], v["ci95"]) for k, v in R["contrasts_T_S"].items()}}))

def json_dump(o): import json; return json.dumps(o, indent=1)
if __name__ == "__main__": main()
