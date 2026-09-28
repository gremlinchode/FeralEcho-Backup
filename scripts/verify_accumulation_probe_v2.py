#!/usr/bin/env python3
"""Verification for the AP-0 v2 additions (tasks_v2, oracle_b_v2, constructor + content auditor, run_gen, qual pipeline). Temp roots only; mock Ollama; read-only vs production."""
import copy, http.server, json, os, random, re, shutil, subprocess, sys, tempfile, threading
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(REPO)); os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PY = "/Users/richietate/miniforge3/envs/feral_echo/bin/python3"; _TMP = tempfile.mkdtemp(prefix="ap0v2_verify_"); os.environ["AP0_ROOT"] = os.path.join(_TMP, "base")
from app.experiments.accumulation_probe import common, worlds, tasks as T1, tasks_v2 as T2, oracle_b_v2, oracle_runner, constructor as C, qual as Q, prompts
results = []
def check(n, ok, d=""): results.append(bool(ok)); print(("PASS " if ok else "FAIL ") + n + (f"  [{d}]" if d and not ok else ""), flush=True)
taken = set(); W = {k: worlds.make_realization(k, 990000 + i, taken) for i, k in enumerate(("K1", "K2", "K3"))}
T = T2.build_tasks_v2(W)
check("v2 task set: 18 T, 12 S, 18 NEAR, 12 UNREL", {s: sum(1 for t in T if t["split"] == s) for s in ("T", "S", "NEAR", "UNREL")} == {"T": 18, "S": 12, "NEAR": 18, "UNREL": 12})
check("NEAR function names do not reveal split membership (no 'explicit')", not any("explicit" in t["fn"] for t in T if t["split"] == "NEAR"))
check("no NEAR/T/S/UNREL function-name collisions", len({t["fn"] for t in T}) == len(T))
bad = []; eqs = []
for t in T:
    for part in ("VAL", "TEST"):
        cases, eq = T2.make_cases2(t, W, part); eqs += eq; r = T1.task_realization(t, W); b = oracle_b_v2.impl(t["base"], r)
        if any(b(*copy.deepcopy(tuple(c["args"]))) != c["expected"] for c in cases): bad.append((t["task_id"], part, "A/B"))
        if part == "TEST" and not oracle_runner.grade(T2.solution_source(t["base"], t["fn"], r), T2.make_test_code(t["fn"], cases))["passed"]: bad.append((t["task_id"], "ref"))
check("v2: independent implementation agrees on all hidden cases; references pass in the real sandbox; no undetected mutants (incl. text-level)", not bad and not eqs, str(bad[:3] + eqs[:3]))
t0 = next(t for t in T if t["task_id"] == "K1.T3"); c1, _ = T2.make_cases2(t0, W, "TEST"); check("v2 K1.T3 now has cases whose ids are NOT ascending (exercises sorting)", any(list(x) != sorted(x) for x in [[d["id"] for d in c["args"][0]] for c in c1]))
tv, _ = T2.make_cases2(t0, W, "VAL"); check("VAL and TEST case partitions are disjoint streams", not ({repr(c["args"]) for c in tv} & {repr(c["args"]) for c in c1}))
# ---- constructor / auditor
r1, r2, r3 = W["K1"], W["K2"], W["K3"]; good1 = ", ".join(f"{c} -> {v}" for c, v in r1["map"].items())
check("audit K1: correct table exact; one wrong pair not exact", C.audit("K1", r1, good1)["exact"] and not C.audit("K1", r1, good1.replace("open", "hold", 1))["exact"])
byc = {}
for c, v in r1["map"].items(): byc.setdefault(v, []).append(c)
check("audit K1: category-first lists parse", C.audit("K1", r1, "; ".join(f"{v}: {', '.join(cs)}" for v, cs in byc.items()))["exact"])
check("audit K1: missing item detected", C.audit("K1", r1, good1.split(",")[0])["missing_items"] == 5)
check("audit K2: descending exact, ascending-with-cue exact, wrong order not", C.audit("K2", r2, "Priority highest to lowest: " + " > ".join(r2["priority"]))["exact"] and C.audit("K2", r2, "Priority from lowest to highest: " + ", ".join(reversed(r2["priority"])))["exact"] and not C.audit("K2", r2, " > ".join(reversed(r2["priority"])))["exact"])
d3 = {"add": "adds {k}", "sub": "subtracts {k}", "mul": "multiplies by {k}", "set": "sets the state to {k}"}; t3 = "; ".join(f"{e} {d3[t].format(k=k)}" for e, (t, k) in r3["ops"].items())
check("audit K3: correct exact; wrong op / wrong constant not exact; clause bleed does not cross events", C.audit("K3", r3, t3)["exact"] and not C.audit("K3", r3, t3.replace("adds", "subtracts", 1).replace("sets the state to", "adds"))["exact"] and not C.audit("K3", r3, re.sub(r"\d", "9", t3))["exact"])
check("audit flags memorization-style texts (episode syntax copied)", C.audit("K3", r3, "final_state(['x'], 2) -> 5 is what happens")["copies_episode_syntax"])
eng = {k: C.episodes(k, W[k], "R1", random.Random(1)) for k in W}
check("R0 and R1 episodes each uniquely identify the convention (brute force)", all(T1.identifiable(W[k], T1.teaching_episodes(W[k])) and T1.identifiable(W[k], C._r1(k, W[k])) for k in W))
check("A1 (missing evidence) episodes do NOT identify the convention (the missing token is unidentifiable)", not any(T1.identifiable(W[k], [e for e in C._r1(k, W[k]) if C._last_token(k, W[k]) not in repr(e[1])]) for k in W))
check("A2 shuffled order differs from R0 order but same set", all(sorted(C.episodes(k, W[k], "A2", random.Random(3))) == sorted(C.episodes(k, W[k], "R0")) and C.episodes(k, W[k], "A2", random.Random(3)) != C.episodes(k, W[k], "R0") for k in ("K1", "K3")))
u = C.constructor_user("K2", C.episodes("K2", W["K2"], "R0")); check("constructor prompt states 'not established' rule and gives no answer", "not established" in u and not any(x in u for x in (T1.k2_pri(W["K2"]),)))
check("scan_leaks catches a hidden literal placed in a constructor request", Q.scan_leaks([{"id": "x", "system": "", "user": "hello " + "([1, 2, 3, 4, 5, 6, 7, 8, 9, 10],)"}], {"t": {"case_literals": ["([1, 2, 3, 4, 5, 6, 7, 8, 9, 10],)"]}}) == ["x"])
# ---- mock server: constructor + worker
Ws_q = Q.qworlds()
class Mock(http.server.BaseHTTPRequestHandler):
    cmode = "calibrated"
    def log_message(self, *a): pass
    def _send(self, o): b = json.dumps(o).encode(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path == "/api/tags": self._send({"models": [{"name": n, "digest": "d" * 64, "size": 1, "modified_at": "x"} for n in ("qwen2.5-coder:7b", "deepseek-r1:7b")]})
        else: self._send({"version": "mock"})
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"]))); s, u = body["messages"][0]["content"], body["messages"][1]["content"]
        if s == C.CONSTRUCTOR_SYSTEM: self._send({"message": {"content": self.construct(u)}, "done_reason": "stop", "eval_count": 5, "prompt_eval_count": 5, "total_duration": 1}); return
        fn = u.split("Function signature: def ")[1].split("(")[0]; t = next(x for x in T2.build_tasks_v2(Ws_q[0]) if x["fn"] == fn and x["split"] in ("T", "S")); k = t["kind"]; r = None
        for Wf in Ws_q:
            rt = Wf[k]; tbl = {"K1": T1.k1_table, "K2": T1.k2_pri, "K3": T1.k3_table}[k]
            if tbl(rt) in s: r = rt; break
            if tbl(worlds.mismatch(rt)) in s: r = worlds.mismatch(rt); break
            mm = re.search(r"Facts about (\w+): not established", s)
            if mm and any(x in s for x in worlds.tokens(rt)):
                X = mm.group(1)
                r = ({**rt, "map": {**rt["map"], X: X}} if k == "K1" else {**rt, "priority": [x for x in rt["priority"] if x != X]} if k == "K2" else {**rt, "ops": {**rt["ops"], X: ["add", 1]}}); break
        if r is None: r = worlds.naive(Ws_q[0][k])
        # world identity for the naive realization must match the task's tokens: use the world whose tokens appear in the task text
        src = T2.solution_source(t["base"], t["fn"], r)
        self._send({"message": {"content": "```python\n" + src + "```"}, "done_reason": "stop", "eval_count": 5, "prompt_eval_count": 5, "total_duration": 1})
    def construct(self, u):
        kind = next(k for k in ("K1", "K2", "K3") if T1.BASE_SPEC[k] in u); rt = next(Wf[kind] for Wf in Ws_q if any(x in u for x in worlds.tokens(Wf[kind])))
        if self.cmode == "wrong": return T1.procedure_text(worlds.mismatch(rt))
        toks = worlds.tokens(rt); miss = [x for x in toks if x not in u]
        if self.cmode == "calibrated" and miss:
            tok = miss[0]; txt = T1.procedure_text(rt)
            if kind == "K1": txt = txt.replace(f"{tok}->{rt['map'][tok]}, ", "").replace(f", {tok}->{rt['map'][tok]}", "")
            elif kind == "K2": txt = txt.replace(f"{tok} > ", "").replace(f" > {tok}", "")
            else: txt = re.sub(rf"{tok}: [^;.]*[;.]\s*", "", txt)
            return txt + f" Facts about {tok}: not established."
        return T1.procedure_text(rt)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Mock); threading.Thread(target=srv.serve_forever, daemon=True).start(); os.environ["AP0_OLLAMA_URL"] = f"http://127.0.0.1:{srv.server_address[1]}"
def run(args, env=None): return subprocess.run([PY, "-I", "-B", "app/experiments/accumulation_probe/qual.py"] + args, capture_output=True, text=True, cwd=str(REPO), env={**os.environ, **(env or {})})
val = {k: [f"{k}.T1", f"{k}.T2", f"{k}.S1", f"{k}.S2"] for k in ("K1", "K2", "K3")}; vp = Path(_TMP) / "val.json"; vp.write_text(json.dumps(val))
proto = REPO / "audits" / "2026-09-21_ap0_v2_constructor_qualification_protocol.md"
b = run(["build", "--val-templates", str(vp)]); check("qual build (worlds, VAL tests, constructor requests, leak + token-disjointness assertions)", b.returncode == 0, b.stdout[-200:] + b.stderr[-300:])
fz = run(["freeze", "--protocol", str(proto)]); check("qual freeze (asserts the protocol text states every decision constant)", fz.returncode == 0 and "QUAL FROZEN" in fz.stdout, fz.stdout[-200:] + fz.stderr[-300:])
base = Path(os.environ["AP0_ROOT"]); reqs = json.loads((base / "v2/qual/roots/construct/inputs/requests.json").read_text())
check("constructor request count = 2 worlds x 3 kinds x (2x3 main + 3x2 adversarial) = 72", len(reqs) == 72)
def pipeline(mode):
    root = Path(_TMP) / f"q_{mode}"; shutil.copytree(base, root); env = {"AP0_ROOT": str(root)}; Mock.cmode = mode
    steps = [run(["construct"], env), run(["build-gate"], env), run(["gate"], env), run(["analyze"], env)]
    sp = root / "v2/qual/results/primary/summary.json"; return root, steps, (json.loads(sp.read_text()) if sp.exists() else None)
rootC, stC, sC = pipeline("calibrated")
check("pipeline (calibrated mock constructor) runs end to end", sC is not None, "".join(s.stderr[-300:] for s in stC))
if sC:
    check("calibrated: every kind QUALIFIED, gate qualified, overall QUALIFIED", all(v["status"] == "QUALIFIED" for v in sC["decision"].values()) and sC["gate_qualification"]["qualified"] and sC["overall"] == "QUALIFIED", str(sC["decision"]) + str(sC["gate_qualification"]))
    check("calibrated: GOLD controls pass the gate, WRONG and NONE controls fail it", sC["controls"]["GOLD"]["gate_pass"] == sC["controls"]["GOLD"]["n"] and sC["controls"]["WRONG"]["gate_pass"] == 0 and sC["controls"]["NONE"]["gate_pass"] == 0, str(sC["controls"]))
    check("calibrated: A1 drafts hedge and the gate rejects the incomplete procedures (no unsafe accepts)", all(sC["adversarial"][k]["A1"]["unsafe_accepts"] == 0 and sC["adversarial"][k]["A1"]["gate_pass"] == 0 for k in ("K1", "K2", "K3")), str(sC["adversarial"]))
rootW, stW, sW = pipeline("wrong")
check("wrong constructor: NOT QUALIFIED overall and the gate rejects the drafts", sW is not None and sW["overall"] == "NOT QUALIFIED" and all(v["R0"]["gate_pass"] == 0 for v in sW["per_kind"].values()), str(sW["decision"] if sW else ""))
rootV, stV, sV = pipeline("clairvoyant")
check("clairvoyant constructor (asserts unsupported facts on missing evidence): flagged unsafe -> not QUALIFIED", sV is not None and all(v["status"] != "QUALIFIED" for v in sV["decision"].values()) and all(sV["adversarial"][k]["A1"]["unsafe_accepts"] > 0 for k in ("K1", "K2", "K3")), str(sV["adversarial"] if sV else ""))
# ---- auditor v2 (post-hoc correction of the frozen K1 parser; see audit_v2.py docstring)
from app.experiments.accumulation_probe import audit_v2 as AV2, constructor as CV1
_r = {"codes": ["aa", "bb", "cc", "dd", "ee", "ff"], "map": {"aa": "hold", "bb": "hold", "cc": "open", "dd": "open", "ee": "closed", "ff": "closed"}}
_g = "The site categorizes records as follows: - 'aa' and 'bb' are categorized as 'hold' - 'cc' and 'dd' are categorized as 'open' - 'ee' and 'ff' are categorized as 'closed' Any other status is not established."
check("auditor v1 (frozen) false-negatives grouped code lists (the disclosed defect)", CV1.audit("K1", _r, _g)["exact"] is False)
check("auditor v2: grouped 'a and b are hold' lists parse exact, hedge sentence does not swallow them", AV2.audit("K1", _r, _g)["exact"] is True)
check("auditor v2: category-first lists ('hold: aa, bb; ...') parse exact", AV2.audit("K1", _r, "hold: aa, bb; open: cc, dd; closed: ee, ff")["exact"] is True)
check("auditor v2: one wrong assignment is flagged (not exact, wrong=1)", (lambda a: (not a["exact"]) and a["wrong_items"] == 1)(AV2.audit("K1", _r, "'aa' and 'bb' are hold; 'cc', 'dd' and 'ee' are open; 'ff' is closed")))
check("auditor v2: an omitted code is 'missing', never counted correct or wrong", (lambda a: a["missing_items"] == 1 and a["wrong_items"] == 0 and not a["exact"])(AV2.audit("K1", _r, "'aa' and 'bb' are hold; 'cc' and 'dd' are open; 'ee' is closed. 'ff' is not established.")))
check("auditor v2 = auditor v1 for K2/K3 (delegates)", AV2.audit("K3", {"events": ["x"], "ops": {"x": ["add", 2]}}, "x adds 2")["exact"] == CV1.audit("K3", {"events": ["x"], "ops": {"x": ["add", 2]}}, "x adds 2")["exact"])
# ---- isolation of the constructor/gate roots + tamper
from app.experiments.accumulation_probe import jail
probe = f"import os\nres={{}}\nfor n,p in (('read_oracle',{str(base / 'v2/qual/oracle/val_tests.json')!r}),('read_other_root',{str(base / 'v2/qual/roots/gate/inputs/requests.json') if (base / 'v2/qual/roots/gate').exists() else str(base / 'v2/qual/oracle/meta.json')!r})):\n    try: open(p).read(5); res[n]='allowed'\n    except Exception as e: res[n]='denied'\nprint(res)"
pr = jail.run_jailed(["-c", probe], base / "v2/qual/roots/construct", base, 30); check("constructor jail: cannot read the oracle or another root", "'read_oracle': 'denied'" in pr.stdout and "'read_other_root': 'denied'" in pr.stdout, pr.stdout + pr.stderr[-200:])
root2 = Path(_TMP) / "q_tamper"; shutil.copytree(base, root2); os.environ["AP0_ROOT"] = str(root2)
import importlib; importlib.reload(common); importlib.reload(Q); p = root2 / "v2/qual/oracle/val_tests.json"; os.chmod(p, 0o644); p.write_text(p.read_text().replace("K1.T1", "K1.T9", 1))
try: Q.verify_freeze(); ok = False
except AssertionError: ok = True
check("tamper: qual refuses to proceed after a frozen oracle file is modified", ok)
print(f"\n{sum(results)}/{len(results)} checks passed"); srv.shutdown(); sys.exit(0 if all(results) else 1)
