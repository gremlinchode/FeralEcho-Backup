"""AP-0 v2 constructor qualification, CONTINGENCY phase QB (pre-declared in QUAL-1 sec. 5): ONE alternative constructor (deepseek-r1:7b, <think> stripped), failing
conventions only (K2, K3), representation R0 (best of R0/R1 from QA; tie -> R0), identical prompts/worlds/seeds/gate as QA. ONLY deviation (declared before any QB call, recorded in
QB_FREEZE.json): num_predict 3000 instead of 400, because a reasoning model spends most of a 400-token budget inside <think> and would return an empty draft (that would test
the token budget, not the constructor). Main drafts only (3 per world x 2 worlds x 2 conventions = 12); adversarial variants are run only if QB reaches the exact-rate bar.
Never touches Stage 1 material. usage: python -I -B qb.py <build|freeze|construct|build-gate|gate|analyze>"""
import json, sys, time, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import qual, common, prompts, tasks as T1, audit_v2, ollama_client, freeze
from app.experiments.accumulation_probe.common import write_json_new, read_json, read_jsonl, sha256_file, seed_for
Q = qual.Q; QB_MODEL = "deepseek-r1:7b"; QB_KINDS = ("K2", "K3")
QB_OPTIONS = {**qual.CONSTRUCTOR_OPTIONS, "num_predict": 3000}
def build():
    if (Q / "roots" / "qb_construct").exists(): sys.exit("STOP: qb already built")
    qual.verify_freeze(); reqs = read_json(Q / "roots" / "construct" / "inputs" / "requests.json")
    sel = [dict(q, options=QB_OPTIONS) for q in reqs if q["id"].split("|")[1] in QB_KINDS and q["id"].split("|")[3] == "R0"]
    write_json_new(Q / "roots" / "qb_construct" / "inputs" / "requests.json", sel); print("QB constructor requests:", len(sel))
def freeze_qb():
    p = Q / "QB_FREEZE.json"
    if p.exists(): sys.exit("STOP: already frozen")
    mi = ollama_client.model_info(common.OLLAMA_URL, QB_MODEL); assert mi["found"]
    write_json_new(p, {"frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "qual_freeze_sha256": sha256_file(Q / "FREEZE_QUAL.json"), "model": mi, "options": QB_OPTIONS, "requests_sha256": sha256_file(Q / "roots" / "qb_construct" / "inputs" / "requests.json"), "qb_py_sha256": sha256_file(Path(__file__)), "audit_v2_sha256": sha256_file(Path(__file__).parent / "audit_v2.py"), "decision": "QUAL-1 sec.3 rules unchanged; QB reported separately from QA"}); print("QB frozen")
def build_gate():
    qual.verify_freeze(); assert (Q / "QB_FREEZE.json").exists()
    drafts = {r["id"]: qual.clean_draft(r.get("response_text")) for r in read_jsonl(Q / "roots" / "qb_construct" / "calls.jsonl") if "response_text" in r}
    meta = read_json(Q / "oracle" / "meta.json"); tests = read_json(Q / "oracle" / "val_tests.json"); reqs = []; gmeta = {}
    for cid, txt in drafts.items():
        m = meta["requests"][cid]
        if not txt: continue
        for tk in meta["val_templates"][m["kind"]]:
            block = prompts.render_block([{"applies_when": T1.APPLIES[m["kind"]], "procedure": txt}]); t = tests[f"w{m['world']}|{tk}"]; s, u = prompts.build_messages({"spec": t["spec"], "sig": t["sig"]}, block, None)
            rid = f"G|draft|{cid}|{tk}|s0"; reqs.append({"id": rid, "system": s, "user": u, "seed": seed_for("QUALGATE", f"draft|{cid}|{tk}", 0)}); gmeta[rid] = {"gid": f"draft|{cid}", "kind": m["kind"], "world": m["world"], "task": tk, "seed_i": 0}
    write_json_new(Q / "roots" / "qb_gate" / "inputs" / "requests.json", reqs); write_json_new(Q / "roots" / "qb_gate" / "inputs" / "gate_meta.json", gmeta); print("QB gate requests:", len(reqs))
def analyze():
    from app.experiments.accumulation_probe import oracle_runner
    out = Q / "results" / "qb"; assert not out.exists()
    Ws = read_json(Q / "oracle" / "worlds.json"); meta = read_json(Q / "oracle" / "meta.json"); tests = read_json(Q / "oracle" / "val_tests.json")
    dr = {r["id"]: r for r in read_jsonl(Q / "roots" / "qb_construct" / "calls.jsonl") if "response_text" in r}; gm = read_json(Q / "roots" / "qb_gate" / "inputs" / "gate_meta.json"); gres = {}
    for r in read_jsonl(Q / "roots" / "qb_gate" / "calls.jsonl"):
        if "response_text" not in r: continue
        m = gm[r["id"]]; t = tests[f"w{m['world']}|{m['task']}"]; code = oracle_runner.extract_code(r["response_text"], t["fn"]); g = oracle_runner.grade(code, t["test_code"]) if code else {"passed": False}
        gres.setdefault(m["gid"], []).append(bool(g["passed"]))
    rows = []
    for cid, m in meta["requests"].items():
        if m["kind"] not in QB_KINDS or m["rep"] != "R0": continue
        raw = dr.get(cid, {}); text = qual.clean_draft(raw.get("response_text")); a = audit_v2.audit(m["kind"], Ws[m["world"]][m["kind"]], text)
        rows.append({**m, "id": cid, "exact": a["exact"], "items": a["items"], "done_reason": raw.get("done_reason"), "eval_count": raw.get("eval_count"), "empty_after_think_strip": not text, "gate_tasks_passed": sum(gres.get(f"draft|{cid}", [])), "gate_pass": sum(gres.get(f"draft|{cid}", [])) >= qual.GATE_MIN_PASS, "text": text})
    R = {}
    for k in QB_KINDS:
        xs = [x for x in rows if x["kind"] == k]; e = sum(x["exact"] for x in xs); R[k] = {"n": len(xs), "exact": e, "wilson95": qual.wilson(e, len(xs)), "empty_drafts": sum(x["empty_after_think_strip"] for x in xs), "truncated": sum(x["done_reason"] == "length" for x in xs), "gate_pass": sum(x["gate_pass"] for x in xs), "exact_rate": round(e / max(1, len(xs)), 3), "status_by_exact_rule": "NOT QUALIFIED" if e / max(1, len(xs)) <= qual.Q_EXACT_NOT else ("exact-bar met (adversarial phase would follow)" if e / max(1, len(xs)) >= qual.Q_EXACT_QUALIFIED else "PARTIALLY QUALIFIED")}
    out.mkdir(parents=True); write_json_new(out / "drafts_audited.json", rows); write_json_new(out / "summary.json", R); print(json.dumps(R, indent=1))
if __name__ == "__main__":
    ph = sys.argv[1]
    {"build": build, "freeze": freeze_qb, "construct": lambda: sys.exit(qual.run_root("qb_construct", QB_MODEL)), "build-gate": build_gate, "gate": lambda: sys.exit(qual.run_root("qb_gate", common.MODEL)), "analyze": analyze}[ph]()
