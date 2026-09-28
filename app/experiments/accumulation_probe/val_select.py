"""Validation-template selection (QUAL protocol sec. 4, v1.1): rank templates by the Laplace-smoothed pooled H pass rate across Stage 0 (its world) and the v2 dev
world; per convention take the 2 best T and 2 best S (ties: more samples, then lower index). Reads only already-existing H-arm data. usage: python -I -B val_select.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import common
E = common.EXP_ROOT; S0 = E / "stage0" / "results" / "primary" / "grades.jsonl"; D = E / "v2" / "dev" / "calls.jsonl"
tally = {}
for g in common.read_jsonl(S0):
    if g["arm"] in ("H", "H2") and not g["probe"] and g["variant"] == "-": t = tally.setdefault(g["task_id"], [0, 0]); t[0] += 1 if g["passed"] else 0; t[1] += 1
for r in common.read_jsonl(D):
    if r.get("arm") == "H" and "passed" in r and r["split"] in ("T", "S"): t = tally.setdefault(r["task_id"], [0, 0]); t[0] += 1 if r["passed"] else 0; t[1] += 1
score = lambda tid: ((tally[tid][0] + 1) / (tally[tid][1] + 2), tally[tid][1])
out = {}; detail = {}
for k in ("K1", "K2", "K3"):
    for sp in ("T", "S"):
        ts = [t for t in tally if t.startswith(k + ".") and t.split(".")[1][0] == sp]
        ranked = sorted(ts, key=lambda t: (-score(t)[0], -score(t)[1], int(t.split(".")[1][1:]))); out.setdefault(k, []).extend(ranked[:2])
        detail.update({t: {"pooled_pass": f"{tally[t][0]}/{tally[t][1]}", "laplace": round(score(t)[0], 3)} for t in ts})
common.write_json_new(E / "v2" / "dev" / "val_templates_pooled.json", out); common.write_json_new(E / "v2" / "dev" / "val_selection_detail.json", detail); print(out); print({t: d["laplace"] for t, d in sorted(detail.items())})
