"""AP-0 v2 CONSTRUCTOR QUALIFICATION orchestrator (does NOT touch Stage 1 material; QUAL worlds are a separate seed namespace).
Phases: build -> freeze -> construct (jailed) -> build-gate -> gate (jailed) -> analyze.  usage: python -I -B qual.py <phase> [...]"""
import argparse, json, math, os, random, re, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import common, worlds, tasks as T1, tasks_v2 as T2, prompts, constructor as C, jail, oracle_runner, ollama_client, freeze
from app.experiments.accumulation_probe.common import EXP_ROOT, MASTER_SEED, seed_for, write_json_new, read_json, read_jsonl, sha256_obj, sha256_file
Q = EXP_ROOT / "v2" / "qual"; KINDS = ("K1", "K2", "K3"); NW = 2; D_MAIN = 3; D_ADV = 2
CONSTRUCTOR_OPTIONS = {"temperature": 0.5, "top_p": 0.95, "num_predict": 400, "num_ctx": 4096, "repeat_penalty": 1.0}
GATE_MIN_PASS = 2            # retain iff >= 2 of 4 validation tasks pass (1 sample each); >=3 is reported descriptively (gate_strict3)
GATE_SEEDS = 2               # gate control replicates (GOLD/WRONG/NONE)
Q_EXACT_QUALIFIED = 5 / 6; Q_EXACT_NOT = 1 / 6; ADV_UNSAFE_MAX = 0.25; GATE_SENS_MIN = 0.85; GATE_FALSE_ACCEPT_MAX = 0.05
RUN_GEN = str(Path(__file__).parent / "run_gen.py")

def wilson(k, n, z=1.96):
    if n == 0: return [0, 0]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0, c - h), 3), round(min(1, c + h), 3)]
def qworlds():
    taken = set(); out = []
    for w in range(NW): out.append({k: worlds.make_realization(k, MASTER_SEED + 7000 + 10 * i + w, taken) for i, k in enumerate(KINDS)})
    return out
def clean_draft(text):
    t = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S); return re.sub(r"\s+", " ", t).strip()[:1200]

def scan_leaks(reqs, tests):
    lits = [l for t in tests.values() for l in t["case_literals"]]
    return [q["id"] for q in reqs if any(l in q["user"] or l in q["system"] for l in lits)]

def build(val_templates_path):
    if (Q / "oracle").exists(): sys.exit("STOP: qual already built")
    Ws = qworlds(); val = read_json(val_templates_path); reqs = []; meta = {}
    for w, Wf in enumerate(Ws):
        for kind in KINDS:
            r = Wf[kind]
            for rep, nd in (("R0", D_MAIN), ("R1", D_MAIN), ("A1", D_ADV), ("A2", D_ADV), ("A3", D_ADV)):
                for d in range(nd):
                    cid = f"C|{kind}|w{w}|{rep}|d{d}"; rng = random.Random(seed_for("QUAL", cid, 1))
                    other = {"K1": "K2", "K2": "K3", "K3": "K1"}[kind]
                    lines = C.episodes(kind, r, rep, rng=rng, distractor_from=(other, Wf[other]))
                    reqs.append({"id": cid, "system": C.CONSTRUCTOR_SYSTEM, "user": C.constructor_user(kind, lines), "seed": seed_for("QUAL", cid, 0), "options": CONSTRUCTOR_OPTIONS})
                    meta[cid] = {"kind": kind, "world": w, "rep": rep, "draft": d, "n_episodes": len(lines)}
    tests = {}
    for w, Wf in enumerate(Ws):
        T = {t["task_id"]: t for t in T2.build_tasks_v2(Wf)}
        for kind in KINDS:
            for tid in val[kind]:
                t = T[tid]; cases, eq = T2.make_cases2(t, Wf, "VAL"); tests[f"w{w}|{tid}"] = {"fn": t["fn"], "test_code": T2.make_test_code(t["fn"], cases), "spec": t["spec"], "sig": t["sig"], "kind": kind, "task_id": tid, "world": w, "case_literals": [repr(tuple(c["args"])) for c in cases if len(repr(tuple(c["args"]))) > 25], "equivalent_mutants": eq}
    # leakage: constructor prompts must not contain any VAL hidden-case literal
    leaks = scan_leaks(reqs, tests); assert not leaks, f"hidden VAL literal present in constructor requests: {leaks[:3]}"
    used = {x for Wf in Ws for r in Wf.values() for x in worlds.tokens(r)}
    for other in (EXP_ROOT / "stage0" / "oracle" / "worlds.json", EXP_ROOT / "v2" / "dev" / "worlds.json"):
        if other.exists():
            ow = read_json(other); prev = {x for grp in ow.values() for r in grp.values() for x in worlds.tokens(r)}; assert not (used & prev), f"QUAL tokens overlap {other.name}"
    write_json_new(Q / "oracle" / "worlds.json", Ws); write_json_new(Q / "oracle" / "val_tests.json", tests); write_json_new(Q / "oracle" / "meta.json", {"val_templates": val, "requests": meta})
    write_json_new(Q / "roots" / "construct" / "inputs" / "requests.json", reqs)
    print("constructor requests:", len(reqs), "| VAL tests:", len(tests))

def freeze_qual(protocol):
    if (Q / "FREEZE_QUAL.json").exists(): sys.exit("STOP: already frozen")
    porc = freeze.sh(["git", "status", "--porcelain"]); mi = ollama_client.model_info(common.OLLAMA_URL, common.MODEL); cm = ollama_client.model_info(common.OLLAMA_URL, os.environ.get("AP0_CONSTRUCTOR_MODEL", common.MODEL))
    pkg = Path(__file__).parent; files = {str(p.relative_to(Q)): sha256_file(p) for p in sorted(Q.rglob("*")) if p.is_file() and p.name not in ("calls.jsonl", "ABORT")}
    f = {"frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "protocol": {"path": freeze._rel(protocol), "sha256": sha256_file(protocol)}, "git": {"head": freeze.sh(["git", "rev-parse", "HEAD"]).strip(), "porcelain_lines": len(porc.splitlines()), "porcelain_sha256": common.sha256_text(porc)},
         "server": freeze.server_facts(), "worker_model": mi, "constructor_model": cm, "constructor_options": CONSTRUCTOR_OPTIONS, "worker_options": common.OPTIONS,
         "decision_constants": {k: globals()[k] for k in ("GATE_MIN_PASS", "GATE_SEEDS", "Q_EXACT_QUALIFIED", "Q_EXACT_NOT", "ADV_UNSAFE_MAX", "GATE_SENS_MIN", "GATE_FALSE_ACCEPT_MAX", "D_MAIN", "D_ADV", "NW")},
         "code_sha256": {p.name: sha256_file(p) for p in sorted(pkg.glob("*.py"))}, "artifact_sha256": files}
    text = Path(protocol).read_text(); missing = [f"{k} = {v}" for k, v in f["decision_constants"].items() if f"{k} = {v}" not in text]; assert not missing, f"protocol text does not state: {missing}"
    assert cm["found"] and mi["found"]; write_json_new(Q / "FREEZE_QUAL.json", f); print("QUAL FROZEN sha256", sha256_file(Q / "FREEZE_QUAL.json")); print("protocol sha256", f["protocol"]["sha256"])

def verify_freeze():
    f = read_json(Q / "FREEZE_QUAL.json"); now = {str(p.relative_to(Q)): sha256_file(p) for p in sorted(Q.rglob("*")) if p.is_file() and p.name not in ("calls.jsonl", "ABORT")}
    bad = [k for k, v in f["artifact_sha256"].items() if now.get(k) != v]; assert not bad, f"frozen qual artifacts changed: {bad}"
    pkg = Path(__file__).parent; badc = [k for k, v in f["code_sha256"].items() if sha256_file(pkg / k) != v]; assert not badc, f"code changed: {badc}"; return f

def run_root(name, model, timeout=8 * 3600):
    root = Q / "roots" / name; r = jail.run_jailed([RUN_GEN, "--root", str(root), "--model", model], root, EXP_ROOT, timeout); print(r.stdout.strip()[-200:], r.stderr.strip()[-300:], flush=True); return r.returncode

def build_gate():
    f = verify_freeze(); drafts = {r["id"]: clean_draft(r.get("response_text")) for r in read_jsonl(Q / "roots" / "construct" / "calls.jsonl") if "response_text" in r}
    meta = read_json(Q / "oracle" / "meta.json"); tests = read_json(Q / "oracle" / "val_tests.json"); Ws = read_json(Q / "oracle" / "worlds.json"); reqs = []; gmeta = {}
    def add(gid, kind, w, text, tk, seed_i):
        block = prompts.render_block([{"applies_when": T1.APPLIES[kind], "procedure": text}]) if text is not None else None
        t = tests[f"w{w}|{tk}"]; s, u = prompts.build_messages({"spec": t["spec"], "sig": t["sig"]}, block, None)
        rid = f"G|{gid}|{tk}|s{seed_i}"; reqs.append({"id": rid, "system": s, "user": u, "seed": seed_for("QUALGATE", f"{gid}|{tk}", seed_i)}); gmeta[rid] = {"gid": gid, "kind": kind, "world": w, "task": tk, "seed_i": seed_i}
    for cid, m in meta["requests"].items():
        if cid in drafts and drafts[cid]:
            for tk in meta["val_templates"][m["kind"]]: add(f"draft|{cid}", m["kind"], m["world"], drafts[cid], tk, 0)
    for w, Wf in enumerate(Ws):
        for kind in KINDS:
            r = Wf[kind]
            for name, text in (("GOLD", T1.procedure_text(r)), ("WRONG", T1.procedure_text(worlds.mismatch(r))), ("NONE", None)):
                for s in range(GATE_SEEDS):
                    for tk in meta["val_templates"][kind]: add(f"ctl|{name}|{kind}|w{w}", kind, w, text, tk, s)
    write_json_new(Q / "roots" / "gate" / "inputs" / "requests.json", reqs); write_json_new(Q / "roots" / "gate" / "inputs" / "gate_meta.json", gmeta)
    write_json_new(Q / "GATE_INPUTS.json", {"sha256_requests": sha256_file(Q / "roots" / "gate" / "inputs" / "requests.json"), "n": len(reqs), "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "freeze_sha256": sha256_file(Q / "FREEZE_QUAL.json")}); print("gate requests:", len(reqs))

def analyze(tag="primary"):
    out = Q / "results" / tag
    if out.exists(): sys.exit("STOP: results exist; use a new tag")
    f = verify_freeze(); Ws = read_json(Q / "oracle" / "worlds.json"); meta = read_json(Q / "oracle" / "meta.json"); tests = read_json(Q / "oracle" / "val_tests.json")
    drafts = {r["id"]: r for r in read_jsonl(Q / "roots" / "construct" / "calls.jsonl") if "response_text" in r}; gm = read_json(Q / "roots" / "gate" / "inputs" / "gate_meta.json")
    grows = read_jsonl(Q / "roots" / "gate" / "calls.jsonl"); gres = {}
    for r in grows:
        if "response_text" not in r: continue
        m = gm[r["id"]]; t = tests[f"w{m['world']}|{m['task']}"]; code = oracle_runner.extract_code(r["response_text"], t["fn"]); g = oracle_runner.grade(code, t["test_code"]) if code else {"passed": False}
        gres.setdefault(m["gid"], {}).setdefault(m["seed_i"], []).append(bool(g["passed"]))
    gate = lambda gid, s=0: (sum(gres[gid][s]) >= GATE_MIN_PASS) if gid in gres and s in gres[gid] else None
    rows = []
    for cid, m in meta["requests"].items():
        text = clean_draft(drafts[cid]["response_text"]) if cid in drafts else ""; r = Ws[m["world"]][m["kind"]]; a = C.audit(m["kind"], r, text)
        row = {**m, "id": cid, "exact": a["exact"], "items": a["items"], "wrong": a["wrong_items"], "missing": a["missing_items"], "hedges": a["hedges"], "copies_syntax": a["copies_episode_syntax"], "gate_pass": gate(f"draft|{cid}"), "gate_tasks_passed": sum(gres.get(f"draft|{cid}", {}).get(0, [])), "gate_strict3": sum(gres.get(f"draft|{cid}", {}).get(0, [])) >= 3, "text": text}
        rows.append(row)
    R = {"per_kind": {}, "controls": {}, "adversarial": {}}
    for kind in KINDS:
        d = {}
        for rep in ("R0", "R1"):
            xs = [x for x in rows if x["kind"] == kind and x["rep"] == rep]; k = sum(x["exact"] for x in xs); d[rep] = {"n": len(xs), "exact": k, "wilson95": wilson(k, len(xs)), "gate_pass": sum(1 for x in xs if x["gate_pass"]), "exact_and_gate_pass": sum(1 for x in xs if x["exact"] and x["gate_pass"]), "exact_but_gate_fail": sum(1 for x in xs if x["exact"] and not x["gate_pass"]), "inexact_but_gate_pass": sum(1 for x in xs if not x["exact"] and x["gate_pass"])}
        best = max(("R0", "R1"), key=lambda rp: (d[rp]["exact"], rp == "R0")); e = d[best]["exact"] / d[best]["n"]
        R["per_kind"][kind] = {**d, "best_representation": best, "best_exact_rate": round(e, 3)}
        adv = {}
        for rep in ("A1", "A2", "A3"):
            xs = [x for x in rows if x["kind"] == kind and x["rep"] == rep]
            adv[rep] = {"n": len(xs), "exact": sum(x["exact"] for x in xs), "gate_pass": sum(1 for x in xs if x["gate_pass"]), "unsafe_accepts": sum(1 for x in xs if x["gate_pass"] and (x["wrong"] > 0 or (rep == "A1" and x["missing"] == 0 and not x["hedges"]))), "hedged": sum(1 for x in xs if x["hedges"]), "fabricated_missing_token(A1: no 'not established' and asserts every fact)": sum(1 for x in xs if rep == "A1" and x["missing"] == 0 and not x["hedges"])}
        R["adversarial"][kind] = adv
    ctl = {"GOLD": [], "WRONG": [], "NONE": []}
    for gid, byseed in gres.items():
        if gid.startswith("ctl|"):
            _, name, kind, w = gid.split("|")
            for s, v in byseed.items(): ctl[name].append({"kind": kind, "world": w, "seed": s, "pass": sum(v) >= GATE_MIN_PASS, "pass_strict3": sum(v) >= 3, "tasks_passed": sum(v)})
    R["controls"] = {n: {"n": len(v), "gate_pass": sum(x["pass"] for x in v), "gate_pass_strict3_descriptive": sum(x["pass_strict3"] for x in v), "tasks_passed_each": [x["tasks_passed"] for x in v], "by_kind": {k: f"{sum(x['pass'] for x in v if x['kind'] == k)}/{sum(1 for x in v if x['kind'] == k)}" for k in KINDS}} for n, v in ctl.items()}
    sens = R["controls"]["GOLD"]["gate_pass"] / max(1, R["controls"]["GOLD"]["n"]); fa = (R["controls"]["WRONG"]["gate_pass"] + R["controls"]["NONE"]["gate_pass"]) / max(1, R["controls"]["WRONG"]["n"] + R["controls"]["NONE"]["n"])
    R["gate_qualification"] = {"sensitivity_GOLD": round(sens, 3), "false_accept_WRONG_NONE": round(fa, 3), "qualified": sens >= GATE_SENS_MIN and fa <= GATE_FALSE_ACCEPT_MAX}
    status = {}
    for kind in KINDS:
        e = R["per_kind"][kind]["best_exact_rate"]; adv = R["adversarial"][kind]["A1"]; unsafe = sum(R["adversarial"][kind][x]["unsafe_accepts"] for x in ("A1", "A2", "A3")) / max(1, sum(R["adversarial"][kind][x]["n"] for x in ("A1", "A2", "A3")))
        if e >= Q_EXACT_QUALIFIED and unsafe <= ADV_UNSAFE_MAX and R["gate_qualification"]["qualified"]: s = "QUALIFIED"
        elif e <= Q_EXACT_NOT: s = "NOT QUALIFIED"
        else: s = "PARTIALLY QUALIFIED"
        status[kind] = {"status": s, "best_representation": R["per_kind"][kind]["best_representation"], "best_exact_rate": e, "adversarial_unsafe_accept_rate": round(unsafe, 3)}
    R["decision"] = status; ks = [v["status"] for v in status.values()]
    R["overall"] = "QUALIFIED" if all(s == "QUALIFIED" for s in ks) else ("NOT QUALIFIED" if all(s == "NOT QUALIFIED" for s in ks) else "PARTIALLY QUALIFIED")
    out.mkdir(parents=True); write_json_new(out / "drafts_audited.json", rows); write_json_new(out / "summary.json", R)
    print(json.dumps({k: R[k] for k in ("per_kind", "controls", "gate_qualification", "decision", "overall")}, indent=1)[:4000])

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("phase"); ap.add_argument("--val-templates"); ap.add_argument("--protocol"); ap.add_argument("--tag", default="primary"); ap.add_argument("--constructor-model", default=None); a = ap.parse_args()
    cm = a.constructor_model or os.environ.get("AP0_CONSTRUCTOR_MODEL", common.MODEL)
    {"build": lambda: build(a.val_templates), "freeze": lambda: freeze_qual(a.protocol), "construct": lambda: sys.exit(run_root("construct", cm)), "build-gate": build_gate, "gate": lambda: sys.exit(run_root("gate", common.MODEL)), "analyze": lambda: analyze(a.tag)}[a.phase]()
