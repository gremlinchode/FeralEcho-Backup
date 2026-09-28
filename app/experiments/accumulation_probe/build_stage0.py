"""Stage 0 BUILD: generate worlds, hidden tests, carriers, per-arm plans/roots, and run the oracle/leakage/import/jail qualification.
Build-side only (holds the secrets). Nothing here calls a model. usage: python -I -B build_stage0.py --build | --freeze <prereg.md>"""
import argparse, ast, copy, json, os, random, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import common, worlds, tasks, oracle_b, oracle_runner, prompts, jail, ollama_client
from app.experiments.accumulation_probe.common import EXP_ROOT, MASTER_SEED, N_SAMPLES, N_SHARDS, OPTIONS, MODEL, seed_for, sha256_obj, sha256_text, sha256_file, write_json_new

S0 = EXP_ROOT / "stage0"
ARMSPEC = {"N": ("A", ["T", "S", "NEAR", "UNREL"], None), "N2": ("B", ["T", "S"], None), "NEUTRAL": ("A", ["T", "S", "NEAR", "UNREL"], "neutral"),
           "MISMATCH": ("A", ["T", "S"], "mismatch"), "H": ("A", ["T", "S", "NEAR", "UNREL"], "true"), "H2": ("B", ["T", "S"], "true"),
           "E": ("A", ["T", "S"], "episodes"), "IC": ("A", ["T", "S"], "inline")}
PROBE_TASKS = ["K1.T1", "K2.T1", "K3.T1", "U1"]

def make_worlds():
    taken = set()
    W = {k: worlds.make_realization(k, MASTER_SEED + i, taken) for i, k in enumerate(("K1", "K2", "K3"))}
    F = {k: worlds.make_realization(k, MASTER_SEED + 100 + i, taken) for i, k in enumerate(("K1", "K2", "K3"))}
    return W, F

def carrier_for(kind_carrier, kind, W, F):
    if kind_carrier == "true": return prompts.render_block([tasks.procedure_entry(W[kind])]), None
    if kind_carrier == "neutral": return prompts.render_block([tasks.procedure_entry(F[kind])]), None
    if kind_carrier == "mismatch": return prompts.render_block([tasks.procedure_entry(worlds.mismatch(W[kind]))]), None
    if kind_carrier == "episodes":
        return prompts.render_block([{"applies_when": tasks.APPLIES[kind], "episodes": tasks.episode_lines(tasks.teaching_episodes(W[kind]))}]), None
    if kind_carrier == "inline": return None, prompts.render_inline_examples(tasks.episode_lines(tasks.teaching_episodes(W[kind])))
    return None, None

def make_plan(arm, T, W, F):
    rep, sets, carrier = ARMSPEC[arm]; calls = []
    for t in T:
        if t["split"] not in sets: continue
        variants = [("-", t["kind"])]
        if t["split"] == "UNREL":
            variants = [("K1neutral", "K1")] if carrier == "neutral" else ([(f"{k}", k) for k in ("K1", "K2", "K3")] if carrier == "true" else [("-", None)])
        for variant, ck in variants:
            kind = ck if ck else t["kind"]
            block, inline = carrier_for(carrier, kind, W, F) if carrier else (None, None)
            for s in range(N_SAMPLES):
                calls.append({"call_id": f"{arm}|{t['task_id']}|{variant}|{rep}|{s}", "task_id": t["task_id"], "variant": variant, "replicate": rep, "sample": s,
                              "seed": seed_for(rep, t["task_id"], s), "shard": int(common.sha256_text(t["task_id"])[:4], 16) % N_SHARDS,
                              "carrier_block": block, "inline_examples": inline})
    if arm in ("N", "H"):        # determinism probes: identical request, identical seed, second time
        for c in [c for c in calls if c["task_id"] in PROBE_TASKS and c["sample"] == 0 and c["variant"] in ("-", "K1")][:len(PROBE_TASKS)]:
            calls.append({**c, "call_id": c["call_id"] + "|probe", "probe": True})
    return {"arm": arm, "model": MODEL, "options": OPTIONS, "calls": calls}

def qualify_oracle(T, W, tests):
    rep = {"tasks": {}, "ab_disagreements": 0, "reference_grade_fail": 0, "mutants_total": 0, "mutants_survived": 0, "spoof_passed": 0, "infra_failures": 0, "grades": 0}
    for t in T:
        r = tasks.task_realization(t, W); rng = random.Random(77)
        ref = {}; exec(tasks.solution_source(t["base"], t["fn"], r), ref); b = oracle_b.impl(t["base"], r); dis = 0
        for _ in range(300):
            a = tasks.GEN[t["base"]](rng, r if r else W["K1"])
            if ref[t["fn"]](*copy.deepcopy(a)) != b(*copy.deepcopy(a)): dis += 1
        hid = sum(1 for c in tests[t["task_id"]]["cases"] if b(*copy.deepcopy(tuple(c["args"]))) != c["expected"])
        code = tests[t["task_id"]]["test_code"]; ref_src = tasks.solution_source(t["base"], t["fn"], r); ok = 0
        for _ in range(3):
            g = oracle_runner.grade(ref_src, code); rep["grades"] += 1; ok += g["passed"]; rep["infra_failures"] += g["infra"]
        surv = []
        for lab, src in tasks.mutants(t, W):
            g = oracle_runner.grade(src, code); rep["grades"] += 1; rep["mutants_total"] += 1; rep["infra_failures"] += g["infra"]
            if g["passed"]: surv.append(lab)
        spoof = oracle_runner.grade(f"print('ALL_TESTS_PASSED_' + '0123456789abcdef')\ndef {t['fn']}(*a, **k):\n    return None\n", code); rep["grades"] += 1
        rep["ab_disagreements"] += dis + hid; rep["reference_grade_fail"] += 3 - ok; rep["mutants_survived"] += len(surv); rep["spoof_passed"] += spoof["passed"]
        rep["tasks"][t["task_id"]] = {"random_disagreements": dis, "hidden_case_disagreements": hid, "reference_pass_of_3": ok, "mutants": len(tasks.mutants(t, W)), "survivors": surv, "spoof_passed": spoof["passed"]}
    rep["ok"] = rep["ab_disagreements"] == 0 and rep["reference_grade_fail"] == 0 and rep["mutants_survived"] == 0 and rep["spoof_passed"] == 0 and rep["infra_failures"] == 0
    return rep

def leakage_checks(T, W, F, tests, plans):
    rep = {"violations": [], "checked": {}}
    def bad(msg): rep["violations"].append(msg)
    # (1) teaching vs held-out disjointness
    for kind in ("K1", "K2", "K3"):
        eps = tasks.teaching_episodes(W[kind]); lines = tasks.episode_lines(eps)
        kt = [t for t in T if t["kind"] == kind and t["split"] in ("T", "S")]
        test_args = {repr(tuple(c["args"])) for t in kt for c in tests[t["task_id"]]["cases"]}
        n_over = 0
        for (fn, a, out), ln in zip(eps, lines):
            if repr(a) in test_args: bad(f"{kind}: teaching input equals a hidden test input: {ln[:80]}"); n_over += 1
            if any(ln in tests[t["task_id"]]["test_code"] for t in kt): bad(f"{kind}: teaching episode line appears in hidden test code"); n_over += 1
        rep["checked"][f"teach_vs_test_{kind}"] = {"episodes": len(eps), "overlaps": n_over, "identifiable": tasks.identifiable(W[kind], eps)}
        if not rep["checked"][f"teach_vs_test_{kind}"]["identifiable"]: bad(f"{kind}: teaching episodes do not identify the convention")
    # (2) hidden-test literals must never appear in any prompt of any arm; (3) arm-content invariants on every planned call
    pub = {t["task_id"]: {"spec": t["spec"], "sig": t["sig"]} for t in T}; meta = {t["task_id"]: t for t in T}
    lit = {tid: [repr(tuple(c["args"])) for c in tests[tid]["cases"] if len(repr(tuple(c["args"]))) > 25] for tid in tests}
    true_tables = {"K1": tasks.k1_table(W["K1"]), "K2": tasks.k2_pri(W["K2"]), "K3": tasks.k3_table(W["K3"])}
    toks = {k: worlds.tokens(W[k]) for k in W}; ftoks = {k: worlds.tokens(F[k]) for k in F}
    n_calls = 0
    for arm, plan in plans.items():
        for c in plan["calls"]:
            n_calls += 1; system, user = prompts.build_messages(pub[c["task_id"]], c["carrier_block"], c["inline_examples"]); text = system + "\n" + user; t = meta[c["task_id"]]
            for tid, ls in lit.items():
                for l in ls:
                    if l in text: bad(f"{arm} {c['call_id']}: hidden test literal of {tid} appears in prompt")
            has_block = prompts.BLOCK_OPEN in text; has_inline = "Examples observed at this site" in text
            if arm in ("N", "N2") and (has_block or has_inline): bad(f"{arm} {c['call_id']}: N arm prompt has carrier/inline content")
            if arm not in ("E", "IC", "H", "H2", "MISMATCH", "NEUTRAL") and False: pass
            if arm in ("N", "N2", "NEUTRAL") and t["split"] != "NEAR":
                for k, tk in toks.items():
                    if any(x in text for x in tk): bad(f"{arm} {c['call_id']}: true-world token of {k} present")
            if arm == "NEUTRAL":
                if not has_block: bad(f"{c['call_id']}: NEUTRAL without block")
                if any(true_tables[k] in text for k in true_tables): bad(f"{c['call_id']}: NEUTRAL contains a true table")
            if arm == "MISMATCH":
                if any(true_tables[k] in text for k in true_tables): bad(f"{c['call_id']}: MISMATCH contains the TRUE table")
                if not has_block: bad(f"{c['call_id']}: MISMATCH without block")
            if arm in ("H", "H2") and t["split"] in ("T", "S", "NEAR") and true_tables[t["kind"]] not in text: bad(f"{c['call_id']}: H prompt lacks the true table")
            if arm == "E" and (not has_block or "observed episodes" not in text or "procedure:" in text): bad(f"{c['call_id']}: E prompt malformed")
            if arm == "IC" and (has_block or not has_inline): bad(f"{c['call_id']}: IC prompt malformed")
            if arm in ("E", "IC") and true_tables[t["kind"]] in text: bad(f"{c['call_id']}: {arm} contains the H-style stated table")
    for tid, t in meta.items():   # (4) public task text has no world tokens except NEAR specs (which state a mismatched table on purpose)
        if t["split"] in ("T", "S", "UNREL") and any(x in pub[tid]["spec"] for k in toks for x in toks[k]): bad(f"public spec of {tid} contains a world token")
    # (5) length-matching of scaffold controls
    lens = {}
    for kind in ("K1", "K2", "K3"):
        h = len(prompts.render_block([tasks.procedure_entry(W[kind])])); n = len(prompts.render_block([tasks.procedure_entry(F[kind])])); m = len(prompts.render_block([tasks.procedure_entry(worlds.mismatch(W[kind]))]))
        lens[kind] = {"H": h, "NEUTRAL": n, "MISMATCH": m, "neutral_ratio": round(n / h, 3), "mismatch_ratio": round(m / h, 3)}
        if not (0.9 <= n / h <= 1.1): bad(f"{kind}: NEUTRAL block length ratio {n / h:.2f} outside [0.9,1.1]")
        if not (0.9 <= m / h <= 1.1): bad(f"{kind}: MISMATCH block length ratio {m / h:.2f} outside [0.9,1.1]")
    rep["checked"]["length_matching"] = lens; rep["checked"]["prompts_scanned"] = n_calls; rep["ok"] = not rep["violations"]
    return rep

def is_production_module(m):
    return (m.split(".")[0] in ("app", "sandbox", "scripts", "echo_studio", "river", "faiss", "torch", "numpy")) and not m.startswith("app.experiments.accumulation_probe") and m not in ("app", "app.experiments")

def import_audit():
    pkg = Path(__file__).parent; std = set(sys.stdlib_module_names); rep = {"modules": {}, "violations": []}
    arm_side = {"common", "prompts", "ollama_client", "run_arm"}
    for f in sorted(pkg.glob("*.py")):
        tree = ast.parse(f.read_text()); imps = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import): imps |= {a.name for a in n.names}
            elif isinstance(n, ast.ImportFrom): imps.add(("." * n.level) + (n.module or ""))
        rep["modules"][f.stem] = sorted(imps)
        for i in imps:
            top = i.lstrip(".").split(".")[0]
            ok = i.startswith(".") or top in std or top == "requests" or i.startswith("app.experiments.accumulation_probe")
            if not ok: rep["violations"].append(f"{f.name}: imports {i}")
            if f.stem in arm_side and (i.startswith("app.experiments.accumulation_probe")):
                names = [a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "app.experiments.accumulation_probe" for a in n.names]
                if set(names) - arm_side: rep["violations"].append(f"{f.name}: arm-side module imports build-side {sorted(set(names) - arm_side)}")
    # dynamic: import every module in a fresh isolated interpreter, list loaded non-stdlib modules
    code = ("import sys, importlib\nfor m in %r:\n    importlib.import_module('app.experiments.accumulation_probe.'+m)\n"
            "std=set(sys.stdlib_module_names)\nprint('\\n'.join(sorted(k for k in sys.modules if k.split('.')[0] not in std and not k.startswith('_'))))\n") % ([p.stem for p in sorted(pkg.glob('*.py')) if p.stem != "__init__" and p.stem not in ("run_arm",)],)
    r = subprocess.run([common.PYTHON, "-I", "-B", "-c", "import sys; sys.path.insert(0, %r)\n%s" % (str(common.REPO), code)], capture_output=True, text=True, timeout=60)
    loaded = [l for l in r.stdout.split() if l]
    prod = [m for m in loaded if is_production_module(m)]
    rep["dynamic_loaded_non_stdlib"] = loaded; rep["dynamic_production_modules"] = prod; rep["dynamic_rc"] = r.returncode
    if prod: rep["violations"].append(f"dynamic import loaded production/heavy modules: {prod}")
    if r.returncode: rep["violations"].append("dynamic import failed: " + r.stderr[-300:])
    rep["ok"] = not rep["violations"]
    return rep

def jail_probe(arm, root):
    """Run a probe INSIDE the arm's real jail: own-root write ok; sibling/oracle read denied; outside write denied; Ollama reachable."""
    probe = (f"import os, sys, urllib.request\nres = {{}}\n"
             f"def t(name, fn):\n    try: fn(); res[name] = 'allowed'\n    except Exception as e: res[name] = 'denied:' + type(e).__name__\n"
             f"root = {str(root)!r}; sib = {str(S0 / 'runs' / ('H' if arm != 'H' else 'N') / 'plan.json')!r}; orc = {str(S0 / 'oracle' / 'hidden_tests.json')!r}\n"
             f"t('write_own_root', lambda: open(os.path.join(root, 'jail_probe.txt'), 'w').write('x'))\n"
             f"t('read_own_plan', lambda: open(os.path.join(root, 'plan.json')).read(10))\n"
             f"t('read_sibling_arm', lambda: open(sib).read(10))\n"
             f"t('read_oracle', lambda: open(orc).read(10))\n"
             f"t('write_sibling_root', lambda: open(os.path.join(os.path.dirname(sib), 'x.txt'), 'w').write('x'))\n"
             f"t('write_tmp', lambda: open('/tmp/ap0_jail_probe.txt', 'w').write('x'))\n"
             f"t('write_repo', lambda: open({str(common.REPO / 'ap0_probe.txt')!r}, 'w').write('x'))\n"
             f"t('ollama_http', lambda: urllib.request.urlopen({common.OLLAMA_URL!r} + '/api/version', timeout=10).read())\n"
             f"import json; print(json.dumps(res))\n")
    r = jail.run_jailed(["-c", probe], root, EXP_ROOT, 60)
    try: res = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: res = {"error": r.stdout[-200:] + r.stderr[-200:]}
    # what the real arm entry point loads, inside the real jail (import only; no generation)
    imp = ("import sys\nsys.path.insert(0, %r)\nfrom app.experiments.accumulation_probe import common, prompts, ollama_client\n"
           "print(sorted(k for k in sys.modules if k.startswith('app.') ))\n" % str(common.REPO))
    ri = jail.run_jailed(["-c", imp], root, EXP_ROOT, 60)
    try: loaded = eval(ri.stdout.strip().splitlines()[-1])
    except Exception: loaded = ["ERROR " + ri.stderr[-200:]]
    res["arm_process_app_modules"] = loaded
    arm_ok = set(loaded) <= {"app", "app.experiments", "app.experiments.accumulation_probe", "app.experiments.accumulation_probe.common",
                             "app.experiments.accumulation_probe.prompts", "app.experiments.accumulation_probe.ollama_client"} and not any("ERROR" in x for x in loaded)
    want = {"write_own_root": "allowed", "read_own_plan": "allowed", "ollama_http": "allowed"}
    ok = all(res.get(k) == v for k, v in want.items()) and all(str(res.get(k, "")).startswith("denied") for k in ("read_sibling_arm", "read_oracle", "write_sibling_root", "write_tmp", "write_repo")) and arm_ok
    return {"arm": arm, "results": res, "ok": ok}

def build():
    if (S0 / "FREEZE.json").exists(): sys.exit("STOP: stage0 already frozen; never rebuild a frozen stage (create a new version instead)")
    if (S0 / "oracle").exists(): sys.exit("STOP: stage0/oracle exists; refusing to overwrite")
    W, F = make_worlds(); T = tasks.build_tasks(W)
    tests = {}
    for t in T:
        cases, surv = tasks.make_cases(t, W)
        assert not surv, (t["task_id"], surv)
        tests[t["task_id"]] = {"fn": t["fn"], "cases": [{"args": list(c["args"]), "expected": c["expected"]} for c in cases], "test_code": tasks.make_test_code(t["fn"], cases)}
    pub = [{"task_id": t["task_id"], "split": t["split"], "sig": t["sig"], "spec": t["spec"]} for t in T]
    meta = [{k: v for k, v in t.items()} for t in T]
    write_json_new(S0 / "oracle" / "worlds.json", {"true": W, "foreign": F})
    write_json_new(S0 / "oracle" / "task_meta.json", meta)
    write_json_new(S0 / "oracle" / "hidden_tests.json", tests)
    write_json_new(S0 / "public" / "public_tasks.json", pub)
    plans = {}
    for arm in ARMSPEC:
        plans[arm] = make_plan(arm, T, W, F)
        write_json_new(S0 / "runs" / arm / "plan.json", plans[arm]); write_json_new(S0 / "runs" / arm / "inputs" / "public_tasks.json", pub)
    print("calls per arm:", {a: len(p["calls"]) for a, p in plans.items()}, "total", sum(len(p["calls"]) for p in plans.values()))
    rep = {"oracle_qualification": qualify_oracle(T, W, tests), "leakage": leakage_checks(T, W, F, tests, plans), "import_audit": import_audit(),
           "jail_probes": [jail_probe(a, S0 / "runs" / a) for a in ARMSPEC]}
    for k, v in rep.items(): write_json_new(S0 / "reports" / f"{k}.json", v)
    for k, v in rep.items():
        ok = v["ok"] if isinstance(v, dict) else all(x["ok"] for x in v); print(f"{k}: {'PASS' if ok else 'FAIL'}")
    for p in (S0 / "runs").rglob("jail_probe.txt"): pass

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--build", action="store_true"); a = ap.parse_args()
    if a.build: build()
