"""Analyze the v2 dev calibration and write the validation-template list by the rule fixed in the QUAL protocol (sec. 4): per convention, the 2 T and 2 S
templates with the highest dev-H pass rate, ties -> lower template index. usage: python -I -B dev_analyze.py"""
import json, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import common
D = common.EXP_ROOT / "v2" / "dev"; rows = [r for r in common.read_jsonl(D / "calls.jsonl") if "passed" in r]
meta = {t["task_id"]: t for t in common.read_json(D / "task_meta.json")}
def rate(arm, tid): x = [1.0 if r["passed"] else 0.0 for r in rows if r["arm"] == arm and r["task_id"] == tid]; return (sum(x) / len(x)) if x else None
out = {"H_TS_by_task": {}, "val_templates": {}, "NEAR": {}, "UNREL": {}, "errors": sum(1 for r in common.read_jsonl(D / "calls.jsonl") if "error" in r)}
for k in ("K1", "K2", "K3"):
    for sp in ("T", "S"):
        ts = sorted([t for t in meta if meta[t]["kind"] == k and meta[t]["split"] == sp], key=lambda t: int(t.split(".")[1][1:]))
        for t in ts: out["H_TS_by_task"][t] = rate("H", t)
        top = sorted(ts, key=lambda t: (-out["H_TS_by_task"][t], int(t.split(".")[1][1:])))[:2]; out["val_templates"].setdefault(k, []).extend(sorted(top, key=lambda t: (t.split(".")[1][0] != "T", int(t.split(".")[1][1:]))))
for k in ("K1", "K2", "K3"):
    ns = [t for t in meta if meta[t]["kind"] == k and meta[t]["split"] == "NEAR"]
    out["NEAR"][k] = {a: round(statistics.mean(rate(a, t) for t in ns), 3) for a in ("N", "NEUTRAL", "H")}; out["NEAR"][k]["per_task"] = {t: [rate("N", t), rate("NEUTRAL", t), rate("H", t)] for t in ns}
un = [t for t in meta if meta[t]["split"] == "UNREL"]; out["UNREL"] = {a: round(statistics.mean(rate(a, t) for t in un), 3) for a in ("N", "H")}; out["UNREL"]["per_task_N_H"] = {t: [rate("N", t), rate("H", t)] for t in un}
out["H_TS_pooled"] = round(statistics.mean(v for v in out["H_TS_by_task"].values()), 3); out["H_TS_by_conv"] = {k: round(statistics.mean(v for t, v in out["H_TS_by_task"].items() if t.startswith(k)), 3) for k in ("K1", "K2", "K3")}
out["NEAR_pooled"] = {a: round(statistics.mean(out["NEAR"][k][a] for k in out["NEAR"]), 3) for a in ("N", "NEUTRAL", "H")}
out["latency_mean_s"] = round(statistics.mean(r["wall_s"] for r in rows), 1); out["truncated"] = sum(r["truncated"] for r in rows); out["infra"] = sum(r["infra"] for r in rows)
common.write_json_new(D / "dev_summary.json", out); common.write_json_new(D / "val_templates.json", out["val_templates"])
print(json.dumps({k: v for k, v in out.items() if k not in ("NEAR", "UNREL")}, indent=1)); print("NEAR", json.dumps({k: {a: v[a] for a in ("N", "NEUTRAL", "H")} for k, v in out["NEAR"].items()})); print("UNREL", {k: v for k, v in out["UNREL"].items() if k != "per_task_N_H"})
