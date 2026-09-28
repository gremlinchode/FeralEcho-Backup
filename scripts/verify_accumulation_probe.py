#!/usr/bin/env python3
"""Verification suite for the AP-0 harness. Read-only against production; every experiment root is a temp dir (AP0_ROOT).
Includes an end-to-end run of the real pipeline (jailed arm processes, sandbox grading) against a MOCK Ollama server with known behaviours,
and adversarial checks (leaks, tampering, spoofing). Run: python scripts/verify_accumulation_probe.py"""
import copy, http.server, json, os, random, shutil, subprocess, sys, tempfile, threading, time
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(REPO)); os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PY = "/Users/richietate/miniforge3/envs/feral_echo/bin/python3"
_TMP = tempfile.mkdtemp(prefix="ap0_verify_"); os.environ["AP0_ROOT"] = os.path.join(_TMP, "base")
from app.experiments.accumulation_probe import common, worlds, tasks, oracle_b, oracle_runner, prompts, build_stage0 as B, grade as G
results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok))); print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""), flush=True)

W, F = B.make_worlds(); T = tasks.build_tasks(W)
# ---- worlds
check("worlds deterministic", B.make_worlds()[0] == W)
check("world tokens are not dictionary words and mutually disjoint", not any(x in worlds._dict_words() for k in list(W.values()) + list(F.values()) for x in worlds.tokens(k)) and len({x for r in list(W.values()) + list(F.values()) for x in worlds.tokens(r)}) == sum(len(worlds.tokens(r)) for r in list(W.values()) + list(F.values())))
check("K2 priority disagrees with alphabetical in exactly 2 adjacent pairs", sum(1 for a, b in zip(W["K2"]["priority"], W["K2"]["priority"][1:]) if a > b) == 2)
check("mismatch differs in every K1 code / reverses K2 / rotates K3", all(worlds.mismatch(W["K1"])["map"][c] != W["K1"]["map"][c] for c in W["K1"]["codes"]) and worlds.mismatch(W["K2"])["priority"] == W["K2"]["priority"][::-1] and all(worlds.mismatch(W["K3"])["ops"][e] != W["K3"]["ops"][e] for e in W["K3"]["events"]))
# ---- tasks / oracle
tests = {}
for t in T:
    cases, surv = tasks.make_cases(t, W); tests[t["task_id"]] = {"fn": t["fn"], "cases": cases, "test_code": tasks.make_test_code(t["fn"], cases)}
    if surv: check(f"mutation kill in-process {t['task_id']}", False, str(surv))
check("every mutant of every task killed in-process (28 tasks)", not any(tasks.make_cases(t, W)[1] for t in T[:1]) and len(T) == 28)
check("teaching episodes identify the convention (brute force) for K1/K2/K3", all(tasks.identifiable(W[k], tasks.teaching_episodes(W[k])) for k in W))
bad = 0
for t in T:
    r = tasks.task_realization(t, W); rng = random.Random(9); ref = {}; exec(tasks.solution_source(t["base"], t["fn"], r), ref); b = oracle_b.impl(t["base"], r)
    for _ in range(150):
        a = tasks.GEN[t["base"]](rng, r if r else W["K1"])
        if ref[t["fn"]](*copy.deepcopy(a)) != b(*copy.deepcopy(a)): bad += 1; break
check("independent implementation agrees with reference on 150 random inputs x 28 tasks", bad == 0)
t0 = T[0]; ref_src = tasks.solution_source(t0["base"], t0["fn"], W["K1"]); tc = tests[t0["task_id"]]["test_code"]
check("sandbox: reference passes", oracle_runner.grade(ref_src, tc)["passed"])
check("sandbox: naive solution fails", not oracle_runner.grade(tasks.solution_source(t0["base"], t0["fn"], worlds.naive(W["K1"])), tc)["passed"])
check("sandbox: nonce spoof (prints a guessed pass line) fails", not oracle_runner.grade("print('ALL_TESTS_PASSED_' + 'deadbeefdeadbeef')\ndef categorize(r):\n    return {}\n", tc)["passed"])
check("sandbox: sys.exit before tests cannot pass", not oracle_runner.grade("import sys\nsys.exit(0)\n" + ref_src, tc)["passed"])
g = oracle_runner.grade("while True:\n    pass\n", tc); check("sandbox: infinite loop -> fail, timeout flagged, not infra", (not g["passed"]) and g["timeout"] and not g["infra"])
check("sandbox: candidate file write is blocked", "PermissionError" in oracle_runner.grade("open('/tmp/ap0_should_not_exist','w').write('x')\n" + ref_src, tc)["error_tail"] + oracle_runner.grade("open('/tmp/ap0_should_not_exist','w').write('x')\n" + ref_src, tc)["output_tail"] or not os.path.exists("/tmp/ap0_should_not_exist"))
check("extract_code: last fenced block wins", oracle_runner.extract_code("a\n```python\nx=1\n```\nb\n```python\ny=2\n```") == "y=2\n")
check("extract_code: prefers the last block that defines the requested function", oracle_runner.extract_code("```python\ndef f(x):\n    return 1\n```\n```python\nprint(f(1))\n```", "f") == "def f(x):\n    return 1\n")
check("extract_code: no code -> empty", oracle_runner.extract_code("I cannot help with that") == "")
# ---- prompts / leakage checker detects injected faults
pl = {a: B.make_plan(a, T, W, F) for a in B.ARMSPEC}
base_rep = B.leakage_checks(T, W, F, tests, {a: copy.deepcopy(p) for a, p in pl.items()})
check("leakage checker passes on the clean plans", base_rep["ok"], str(base_rep["violations"][:2]))
def tampered(mut):
    p = copy.deepcopy(pl); mut(p); return B.leakage_checks(T, W, F, tests, p)
def leak_hidden(p): p["H"]["calls"][0]["carrier_block"] += " " + repr(tuple(tests["K1.T1"]["cases"][0]["args"]))
def n_gets_block(p): p["N"]["calls"][0]["carrier_block"] = pl["H"]["calls"][0]["carrier_block"]
def neutral_gets_true(p): p["NEUTRAL"]["calls"][0]["carrier_block"] = next(c for c in pl["H"]["calls"] if c["task_id"] == p["NEUTRAL"]["calls"][0]["task_id"])["carrier_block"]
def mismatch_gets_true(p): p["MISMATCH"]["calls"][0]["carrier_block"] = next(c for c in pl["H"]["calls"] if c["task_id"] == p["MISMATCH"]["calls"][0]["task_id"])["carrier_block"]
def e_states_table(p): p["E"]["calls"][0]["carrier_block"] += " " + tasks.k1_table(W["K1"])
for nm, m in (("hidden-test literal in a carrier", leak_hidden), ("N arm given a carrier", n_gets_block), ("NEUTRAL given the true table", neutral_gets_true), ("MISMATCH given the true table", mismatch_gets_true), ("E arm states the table", e_states_table)):
    check(f"leakage checker catches: {nm}", not tampered(m)["ok"])
# ---- import audit + predicate positive control
ia = B.import_audit(); check("import audit: no production/heavy module imported (static + dynamic)", ia["ok"], str(ia["violations"]))
check("import audit predicate flags production/heavy modules (positive control)", all(B.is_production_module(m) for m in ("app.core.echo_model_orchestrator", "sandbox.run_script", "scripts.run_capability_pilot", "numpy", "faiss")) and not B.is_production_module("requests") and not B.is_production_module("app.experiments.accumulation_probe.prompts"))
import ast
_tree = ast.parse((REPO / "app/experiments/accumulation_probe/run_arm.py").read_text()); _tree.body = [n for n in _tree.body if not (isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant))]
_code = ast.unparse(_tree)
check("arm entry point CODE (docstring excluded) does not reference hidden tests, oracle, tasks, worlds or solutions", not any(x in _code for x in ("hidden_tests", "oracle", "worlds", "solution", "task_meta", "import tasks")) and {a.name for n in ast.walk(_tree) if isinstance(n, ast.ImportFrom) and n.module == "app.experiments.accumulation_probe" for a in n.names} == {"common", "prompts", "ollama_client"})

# ---- mock Ollama server
class Mock(http.server.BaseHTTPRequestHandler):
    mode = "perfect"; ctx = None
    def log_message(self, *a): pass
    def _send(self, obj): b = json.dumps(obj).encode(); self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path == "/api/tags": self._send({"models": [{"name": "qwen2.5-coder:7b", "digest": "mockdigest" * 6, "size": 1, "modified_at": "x"}]})
        else: self._send({"version": "mock"})
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"]))); sysm, usr = body["messages"][0]["content"], body["messages"][1]["content"]
        c = Mock.ctx; fn = usr.split("Function signature: def ")[1].split("(")[0]; t = next(x for x in c["T"] if x["fn"] == fn); k = t["kind"]; mode = Mock.mode
        tt = {"K1": tasks.k1_table, "K2": tasks.k2_pri, "K3": tasks.k3_table}
        r = None
        if t["split"] == "NEAR": r = tasks.task_realization(t, c["W"]) if mode != "overapply" or tt[k](c["W"][k]) not in sysm else c["W"][k]
        elif t["split"] == "UNREL": r = None
        elif mode == "leaky": r = c["W"][k]
        elif mode == "carrier_blind": r = worlds.naive(c["W"][k])
        else:
            block_true = tt[k](c["W"][k]) in sysm; block_mm = tt[k](worlds.mismatch(c["W"][k])) in sysm and not block_true; episodes = "observed episodes" in sysm; inline = "Examples observed at this site" in usr
            if mode == "inline_only": r = c["W"][k] if inline else worlds.naive(c["W"][k])
            elif block_true or episodes or inline: r = c["W"][k]
            elif block_mm: r = worlds.mismatch(c["W"][k])
            else: r = worlds.naive(c["W"][k])
        src = tasks.solution_source(t["base"], t["fn"], r)
        self._send({"message": {"content": "```python\n" + src + "```"}, "done_reason": "stop", "eval_count": 50, "prompt_eval_count": 100, "total_duration": 1})
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Mock); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["AP0_OLLAMA_URL"] = f"http://127.0.0.1:{port}"; Mock.ctx = {"T": T, "W": W}
def pyrun(args, env=None): return subprocess.run([PY, "-I", "-B"] + args, capture_output=True, text=True, cwd=str(REPO), env={**os.environ, **(env or {})})
prereg = Path(_TMP) / "prereg_test.md"; prereg.write_text("mock preregistration\n" + "".join(f"{n} = {getattr(G, n)}\n" for n in ("HEADROOM_MIN", "HEADROOM_LOWER_MIN", "PER_CONV_HEADROOM", "N_CEILING", "NOISE_MAX", "MISMATCH_GAP_MIN", "REGRADE_AGREE_MIN", "INFRA_MAX", "TRUNC_MAX", "BOOT_N")))
b = pyrun(["app/experiments/accumulation_probe/build_stage0.py", "--build"]); check("mock: full build (worlds, hidden tests, plans, oracle qualification, leakage, import audit, jail probes)", b.returncode == 0 and "FAIL" not in b.stdout, b.stdout[-400:] + b.stderr[-400:])
fz = pyrun(["app/experiments/accumulation_probe/freeze.py", "--prereg", str(prereg), "--verify-script", str(REPO / "scripts" / "verify_accumulation_probe.py")]); check("mock: freeze writes FREEZE.json with hashes", fz.returncode == 0 and "FROZEN" in fz.stdout, fz.stdout[-300:] + fz.stderr[-300:])
base = Path(os.environ["AP0_ROOT"]); fj = json.loads((base / "stage0" / "FREEZE.json").read_text())
check("FREEZE records git head, porcelain, server, model digest, prereg hash, code hashes, artifact hashes", all(k in fj for k in ("git", "server", "model", "preregistration", "code_sha256", "artifact_sha256")) and fj["model"]["digest"] and fj["git"]["head"])
check("refuses to rebuild a frozen stage", pyrun(["app/experiments/accumulation_probe/build_stage0.py", "--build"]).returncode != 0)
def pipeline(mode):
    root = Path(_TMP) / f"run_{mode}"; shutil.copytree(base, root); env = {"AP0_ROOT": str(root)}; Mock.mode = mode
    r = pyrun(["app/experiments/accumulation_probe/stage0.py", "run"], env); g = pyrun(["app/experiments/accumulation_probe/grade.py"], env)
    m = json.loads((root / "stage0" / "results" / "primary" / "metrics.json").read_text()) if (root / "stage0" / "results" / "primary" / "metrics.json").exists() else None
    return root, r, g, m
rootP, rP, gP, mP = pipeline("perfect")
check("mock perfect consumer: run completes", rP.returncode == 0 and mP is not None, rP.stdout[-300:] + rP.stderr[-300:] + gP.stderr[-400:])
if mP:
    R = mP["metrics"]; V = mP["verdict"]; pr = R["pass_rates_T_S"]
    check("perfect: H>=0.95, E>=0.95, IC>=0.95, N<=0.05, NEUTRAL<=0.05, MISMATCH<=0.05", pr["H"] >= .95 and pr["E"] >= .95 and pr["IC"] >= .95 and pr["N"] <= .05 and pr["NEUTRAL"] <= .05 and pr["MISMATCH"] <= .05, str(pr))
    check("perfect: replicate arms N2/H2 match N/H (noise floor ~0)", abs(pr["N"] - pr["N2"]) <= .02 and abs(pr["H"] - pr["H2"]) <= .02)
    check("perfect: negative controls behave (NEAR/UNREL pass everywhere)", all(R["negative_controls"][s][a]["pass_rate"] >= .95 for s in ("NEAR", "UNREL") for a in ("N", "NEUTRAL", "H")), str(R["negative_controls"]))
    check("perfect: runtime score == independent re-grade for every response; request checks ok", R["oracle_agreement"]["runtime_vs_regrade_agreement"] == 1.0 and R["integrity"]["request_checks"]["ok"], str(R["integrity"]["request_checks"]["violations"][:2]))
    check("perfect: determinism probes present", R["determinism_probe"]["pairs"] == 8, str(R["determinism_probe"]))
    check("perfect: verdict INFORMATIVE, worker CAN use carrier", V["verdict"] == "INFORMATIVE" and V["can_this_worker_use_this_carrier"] == "YES", str(V))
for mode, expect_diag in (("carrier_blind", "WORKER/TASK/INSTRUMENT"), ("inline_only", "FORMAT-CONSUMPTION")):
    root, r, g_, m = pipeline(mode)
    check(f"mock {mode}: UNINFORMATIVE with correct diagnostic", m is not None and m["verdict"]["verdict"] == "UNINFORMATIVE" and expect_diag in (m["verdict"]["diagnostic_if_g1_fails"] or ""), str(m["verdict"] if m else g_.stderr[-300:]))
root, r, g_, m = pipeline("leaky")
check("mock leaky (answers without any carrier): UNINFORMATIVE (N above ceiling / no headroom)", m is not None and m["verdict"]["verdict"] == "UNINFORMATIVE", str(m["verdict"] if m else ""))
root, r, g_, m = pipeline("overapply")
check("mock overapply: near-match negative control exposes carrier over-application (H below N on NEAR)", m is not None and m["metrics"]["negative_controls"]["NEAR"]["H_minus_N"] < -0.5, str(m["metrics"]["negative_controls"]["NEAR"] if m else ""))
# ---- tamper / integrity attacks against the completed perfect run
sys.path.insert(0, str(REPO)); f_, meta_, tests_, W_, pub_, plans_, rows_ = (lambda: None, None, None, None, None, None, None)
os.environ["AP0_ROOT"] = str(rootP)
import importlib; importlib.reload(common); 
from app.experiments.accumulation_probe import stage0 as S; importlib.reload(S)
G.S0 = S.S0 = common.EXP_ROOT / "stage0"
f_, meta_, tests_, W_, pub_, plans_, rows_ = G.load()
check("ledger hash chains verify on untouched rows", G.check_chain(rows_) == [])
rt = copy.deepcopy(rows_); rt["H"][3]["response_text"] = "```python\ndef x():\n    pass\n```"; check("tamper: edited response breaks the hash chain", G.check_chain(rt) != [])
rt = copy.deepcopy(rows_); del rt["N"][5]; check("tamper: deleted row breaks the hash chain", G.check_chain(rt) != [])
rt = copy.deepcopy(rows_); rt["N"][2]["request"]["messages"][0]["content"] += tests_["K1.T1"]["cases"][0]["args"].__repr__(); check("tamper: prompt edited after the fact is flagged (request hash + leak check)", not G.check_requests(rt, plans_, pub_, meta_, tests_, W_)["ok"])
# frozen-artifact tamper
root2 = Path(_TMP) / "tamper"; shutil.copytree(base, root2); os.environ["AP0_ROOT"] = str(root2); importlib.reload(common); importlib.reload(S)
p = root2 / "stage0" / "runs" / "N" / "plan.json"; os.chmod(p, 0o644); p.write_text(p.read_text().replace('"K1.T1"', '"K1.T9"', 1))
try: S.verify_freeze(); ok = False
except AssertionError: ok = True
check("tamper: stage0 refuses to run after a frozen plan is modified", ok)
print(f"\n{sum(1 for _, o in results if o)}/{len(results)} checks passed"); srv.shutdown()
sys.exit(0 if all(o for _, o in results) else 1)
