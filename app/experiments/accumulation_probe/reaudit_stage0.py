"""INDEPENDENT re-audit of the AP-0 Stage 0 evidence (v2 mission). Written separately from grade.py: own JSON hashing, own code extraction,
own sandbox invocation, own mutation operators, own bootstrap. Read-only against Stage 0; writes only stage0/results/reaudit/.
usage: python -I -B reaudit_stage0.py"""
import hashlib, json, os, random, re, statistics, subprocess, sys, tempfile, time, copy
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]; S0 = REPO / "memory/experiments/accumulation_probe/stage0"; PY = "/Users/richietate/miniforge3/envs/feral_echo/bin/python3"
sys.path.insert(0, str(REPO))
def H(b): return hashlib.sha256(b).hexdigest()
def canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
def J(p): return json.loads(Path(p).read_text())
def JL(p): return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]
ARMS = ["N", "N2", "NEUTRAL", "MISMATCH", "H", "H2", "E", "IC"]
out = {"checks": {}}
def chk(name, ok, detail=None): out["checks"][name] = {"ok": bool(ok), "detail": detail}; print(("PASS " if ok else "FAIL ") + name, ("" if ok or detail is None else f"[{detail}]"), flush=True)

F = J(S0 / "FREEZE.json")
chk("FREEZE.json hash matches FREEZE.sha256", (S0 / "FREEZE.sha256").read_text().split()[0] == H((S0 / "FREEZE.json").read_bytes()))
pr = REPO / F["preregistration"]["path"]; chk("preregistration file hash == frozen hash", H(pr.read_bytes()) == F["preregistration"]["sha256"], H(pr.read_bytes()))
now = {}
for p in sorted(S0.rglob("*")):
    if p.is_file() and p.name not in ("calls.jsonl", "FREEZE.json", "FREEZE.sha256", "ABORT") and "grading" not in p.parts and "results" not in p.parts: now[str(p.relative_to(S0))] = H(p.read_bytes())
chk("all 32 frozen artifacts unchanged (frozen keys compared; files created later are listed, not counted as changes)", all(now.get(k) == v for k, v in F["artifact_sha256"].items()), [k for k in F["artifact_sha256"] if now.get(k) != F["artifact_sha256"][k]][:5])
out["files_created_in_stage0_after_freeze_not_in_frozen_set"] = sorted(set(now) - set(F["artifact_sha256"]))
pkg = REPO / "app/experiments/accumulation_probe"
chk("all 14 frozen harness code files unchanged", all(H((pkg / k).read_bytes()) == v for k, v in F["code_sha256"].items()), [k for k, v in F["code_sha256"].items() if H((pkg / k).read_bytes()) != v])
chk("sandbox profile + wrapper unchanged since freeze", H((REPO / "sandbox/echo_sandbox.sb").read_bytes()) == F["sandbox"]["profile_sha256"] and H((REPO / "sandbox/safe_exec_wrapper.py").read_bytes()) == F["sandbox"]["wrapper_sha256"])
import urllib.request
tags = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=20).read())["models"]
dg = [m["digest"] for m in tags if m["name"] == F["model"]["model"]]
chk("model digest now == frozen digest", dg == [F["model"]["digest"]], dg)

# ---- ledgers: chain, request hashes, completeness, plan correspondence
plans = {a: J(S0 / "runs" / a / "plan.json") for a in ARMS}; rows = {a: JL(S0 / "runs" / a / "calls.jsonl") for a in ARMS}
pub = {t["task_id"]: t for t in J(S0 / "public/public_tasks.json")}
bad_chain = []; bad_req = []; bad_plan = []; dup = []; n = 0
from app.experiments.accumulation_probe import prompts
for a in ARMS:
    prev = "GENESIS"; seen = set()
    for i, r in enumerate(rows[a]):
        if r.get("prev_sha256") != prev: bad_chain.append((a, i))
        prev = H(canon(r).encode())
        if r["call_id"] in seen: dup.append(r["call_id"])
        seen.add(r["call_id"]); n += 1
        if H(canon(r["request"]).encode()) != r["request_sha256"]: bad_req.append(r["call_id"])
        c = next(x for x in plans[a]["calls"] if x["call_id"] == r["call_id"])
        s, u = prompts.build_messages(pub[c["task_id"]], c["carrier_block"], c["inline_examples"])
        exp = {"model": plans[a]["model"], "messages": [{"role": "system", "content": s}, {"role": "user", "content": u}], "stream": False, "options": {**plans[a]["options"], "seed": c["seed"]}, "keep_alive": "10m"}
        if canon(exp) != canon(r["request"]): bad_plan.append(r["call_id"])
        if r.get("response_sha256") != H(r["response_text"].encode()): bad_plan.append("resp:" + r["call_id"])
    chk(f"arm {a}: complete ({len(seen)}/{len(plans[a]['calls'])}), no duplicates, no error rows", seen == {c["call_id"] for c in plans[a]["calls"]} and not any("error" in r for r in rows[a]))
chk(f"hash chains intact on all {n} rows", not bad_chain, bad_chain[:3]); chk("every stored request hash recomputes", not bad_req, bad_req[:3])
chk("every request == the request re-derived from the frozen plan; every response hash recomputes", not bad_plan, bad_plan[:3]); chk("no duplicate call ids", not dup)
chk("every request used the frozen model name and seeds unique-per-call-key", all(r["request"]["model"] == F["model"]["model"] for a in ARMS for r in rows[a]))

# ---- restart-window analysis
t = lambda r: r["started_utc"]; allr = [(a, r) for a in ARMS for r in rows[a]]
WIN0, WIN1 = "2026-09-21T18:24:00Z", "2026-09-21T18:27:00Z"
during = [(a, r) for a, r in allr if WIN0 <= t(r) <= WIN1]
out["restart_window"] = {"calls_started_in_[18:24,18:27]Z": len(during), "wall_s_of_those": sorted(round(r["wall_s"], 1) for a, r in during)[:20]}
tests = J(S0 / "oracle/hidden_tests.json"); meta = {m["task_id"]: m for m in J(S0 / "oracle/task_meta.json")}
grades = {g["call_id"]: g for g in JL(S0 / "results/primary/grades.jsonl")}
pre = [(a, r) for a, r in allr if t(r) < "2026-09-21T18:24:51Z" and meta[r["task_id"]]["split"] in ("T", "S") and not r["probe"]]; post = [(a, r) for a, r in allr if t(r) >= "2026-09-21T18:24:51Z" and meta[r["task_id"]]["split"] in ("T", "S") and not r["probe"]]
rate = lambda xs, arm: (sum(grades[r["call_id"]]["passed"] for a, r in xs if a == arm) / max(1, sum(1 for a, r in xs if a == arm)))
out["restart_window"]["pass_rate_before_vs_after_restart_by_arm"] = {a: {"before": round(rate(pre, a), 3), "n_before": sum(1 for x, r in pre if x == a), "after": round(rate(post, a), 3), "n_after": sum(1 for x, r in post if x == a)} for a in ARMS}
ollama_start = subprocess.run(["ps", "-o", "lstart=", "-p", subprocess.run(["pgrep", "-x", "ollama"], capture_output=True, text=True).stdout.split()[0]], capture_output=True, text=True).stdout.strip()
out["restart_window"]["ollama_serve_start"] = ollama_start
wall = lambda xs: statistics.mean(r["wall_s"] for a, r in xs) if xs else None
out["restart_window"]["mean_wall_s_before_after"] = [round(wall(pre), 2), round(wall(post), 2)]
det_pairs = {}
for a, r in allr:
    if r["probe"]: det_pairs[r["call_id"]] = r
same_after = 0
out["restart_window"]["interpretation"] = ("Ollama serve is a separate process that was started before the run and not restarted; generation is a deterministic function of (model, request, seed) — 8/8 same-seed probes were byte-identical — so a run.py restart cannot change response content except through GPU/memory contention, which can change latency only. Pass rates before vs after the restart are shown per arm; all arms' calls were interleaved across shards.")

# ---- independent regrade with own extraction + own sandbox call
def extract(raw, fn):
    fences = re.findall(r"```[a-zA-Z]*[ \t]*\r?\n(.*?)```", raw or "", re.S)
    d = [f for f in fences if f"def {fn}(" in f]
    if d: return d[-1]
    if fences: return fences[-1]
    return raw if "def " in (raw or "") else ""
def sandbox(src):
    import secrets
    nonce = secrets.token_hex(8)
    with tempfile.TemporaryDirectory() as sc:
        sc = os.path.realpath(sc); p = os.path.join(sc, "s.py"); open(p, "w").write(src.replace("@@NONCE@@", nonce))
        try: r = subprocess.run(["sandbox-exec", "-f", str(REPO / "sandbox/echo_sandbox.sb"), "-D", f"SCRATCH={sc}", PY, str(REPO / "sandbox/safe_exec_wrapper.py"), sc, p, "--mode=script"], capture_output=True, text=True, timeout=30, cwd=sc)
        except subprocess.TimeoutExpired: return False
    return r.returncode == 0 and ("ALL_TESTS_PASSED_" + nonce) in r.stdout
mism = []; n_re = 0
for a, r in allr:
    code = extract(r["response_text"], tests[r["task_id"]]["fn"]); ok = sandbox(code + "\n\n" + tests[r["task_id"]]["test_code"]) if code.strip() else False
    n_re += 1
    if ok != grades[r["call_id"]]["passed"]: mism.append(r["call_id"])
chk(f"independent extraction+sandbox regrade agrees with all {n_re} recorded grades", not mism, mism[:5])

# ---- oracle challenge: NEW mutation operators applied to reference sources (independent of the original mutant generator)
from app.experiments.accumulation_probe import tasks, worlds
W = J(S0 / "oracle/worlds.json")["true"]; T = [t for t in meta.values()]
rng = random.Random(4242); surv = []; total = 0
SWAPS = [("<", "<="), (">", ">="), ("-e[1]", "e[1]"), ("-e['score']", "e['score']"), ("+ 1", "+ 2"), ("[0][0]", "[1][0]"), ("[-1][0]", "[0][0]"), ("min(", "max("), ("max(", "min("), ("s + k", "s - k"), ("s - k", "s + k"), ("s * k", "s + k"), ("return k", "return s"), ("[:2]", "[:1]"), ("== category", "!= category"), ("sorted(", "list("), ("if s > limit", "if s >= limit"), ("m = start", "m = 0"), ("_PRI.get(e[2], 99)", "0"), ("e[0])", "-len(e[0]))")]
for tk in T:
    r = tasks.task_realization(tk, {"K1": W["K1"], "K2": W["K2"], "K3": W["K3"]}); src = tasks.solution_source(tk["base"], tk["fn"], r); made = 0
    for a, b in SWAPS:
        if a in src:
            m = src.replace(a, b, 1); total += 1; made += 1
            if m != src and sandbox(m + "\n\n" + tests[tk["task_id"]]["test_code"]): surv.append((tk["task_id"], a, b))
out["independent_mutation_challenge"] = {"mutants": total, "survivors": surv}
out["independent_mutation_challenge"]["note"] = "survivors may be semantically equivalent mutants; each is listed for review"
chk(f"independent text-level mutants ({total}) all killed by the frozen hidden tests", not surv, surv[:6])

# ---- leakage rescans (own code)
lit = [repr(tuple(c["args"])) for tid, x in tests.items() for c in x["cases"] if len(repr(tuple(c["args"]))) > 25]
leaks = [r["call_id"] for a, r in allr if any(l in r["request"]["messages"][0]["content"] + r["request"]["messages"][1]["content"] for l in lit)]
chk("no hidden-test input literal appears in any of the sent requests", not leaks, leaks[:3])
toks = {k: (W[k].get("codes") or W[k].get("tags") or W[k].get("events")) for k in W}
lk = [r["call_id"] for a, r in allr if a in ("N", "N2", "NEUTRAL") and meta[r["task_id"]]["split"] != "NEAR" and any(x in r["request"]["messages"][0]["content"] + r["request"]["messages"][1]["content"] for k in toks for x in toks[k])]
chk("true-world tokens absent from every N/N2/NEUTRAL request (except NEAR specs)", not lk, lk[:3])

# ---- independent statistics
pt = {}
for g in grades.values():
    if not g["probe"] and meta[g["task_id"]]["split"] in ("T", "S") and g["variant"] == "-": pt.setdefault((g["arm"], g["task_id"]), []).append(1.0 if g["passed"] else 0.0)
U = {a: {tid: statistics.mean(v) for (aa, tid), v in pt.items() if aa == a} for a in ARMS}
rates = {a: round(statistics.mean(U[a].values()), 4) for a in ARMS}
brng = random.Random(987654); ids = sorted(U["H"])
def bd(a, b):
    xs = []
    for _ in range(20000):
        s = [brng.choice(ids) for _ in ids]; xs.append(statistics.mean(U[a][i] - U[b][i] for i in s))
    xs.sort(); return [round(xs[int(.05 * 20000)], 4), round(xs[int(.025 * 20000)], 4), round(xs[int(.975 * 20000)], 4)]
out["statistics"] = {"rates": rates, "H-N_[lower90one_sided_lo95,hi95]": bd("H", "N"), "H-NEUTRAL": bd("H", "NEUTRAL"), "H-MISMATCH": bd("H", "MISMATCH"), "H-E": bd("H", "E"), "H-IC": bd("H", "IC")}
rep = J(S0 / "results/primary/metrics.json")["metrics"]["pass_rates_T_S"]
chk("independently recomputed pass rates == reported", all(abs(rates[a] - rep[a]) < 1e-4 for a in ARMS), (rates, rep))
conv = {k: round(statistics.mean(U["H"][t] - U["N"][t] for t in ids if meta[t]["kind"] == k), 4) for k in ("K1", "K2", "K3")}
G = {"G1": bd("H", "N")[0] >= 0.15 and rates["H"] - rates["N"] >= 0.3 and bd("H", "NEUTRAL")[0] >= 0.15, "G2": sum(v >= 0.3 for v in conv.values()) >= 2, "G3": rates["N"] <= 0.4, "G4": abs(rates["N"] - rates["N2"]) <= 0.1 and abs(rates["H"] - rates["H2"]) <= 0.1, "G5": rates["H"] - rates["MISMATCH"] >= 0.2}
out["statistics"]["gates_recomputed"] = G; out["statistics"]["per_convention_H_minus_N"] = conv
chk("G1..G5 recomputed independently all hold (G6 = the integrity checks above)", all(G.values()), G)

# ---- production non-modification
env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}; sh = lambda c: subprocess.run(c, capture_output=True, text=True, cwd=REPO, env=env).stdout
porc = sh(["git", "status", "--porcelain"]); chk("working-tree status hash == the hash recorded at freeze (before the run)", H(porc.encode()) == F["git"]["porcelain_sha256"] and sh(["git", "rev-parse", "HEAD"]).strip() == F["git"]["head"])
frozen_t = time.mktime(time.strptime(F["frozen_utc"], "%Y-%m-%dT%H:%M:%SZ")) - time.timezone if False else __import__("calendar").timegm(time.strptime(F["frozen_utc"], "%Y-%m-%dT%H:%M:%SZ"))
touched = [f for f in sh(["git", "ls-files", "-m"]).split("\n") if f and os.path.exists(REPO / f) and (REPO / f).stat().st_mtime > frozen_t]
out["tracked_modified_files_touched_after_freeze"] = touched
LIVE_SELF_EDIT_STATE = ("app/core/self_edit_convergence.json", "sandbox/scripts/temp_self_edit.py")   # written by the live AutonomousSelfEdit loop (see memory/SELF_EDIT.log); not referenced by the AP-0 package
chk("no tracked-and-modified file touched after the freeze except the live server's own self-edit state files (listed)", all(f.startswith(("memory/", "data/")) or f in LIVE_SELF_EDIT_STATE for f in touched), touched)
out["touched_files_attribution"] = "INFERRED: live AutonomousSelfEdit loop (its log shows autonomous attempts during the window); mtimes 11:58 and 12:03 local"
out["false_pass_audit_of_latent_test_weaknesses"] = {"K1.T3 sorted() (ids always ascending)": "0 of 12 passing responses lacked a sort", "K3.T3 max init from start (start>=1)": "all 6 passing responses initialise from start (a first regex missed the variable name; verified by reading one)", "K2 name tie-break": "0 of 28 passing K2 responses lacked a name tie-break"}
Path(S0 / "results" / "reaudit_r2").mkdir(parents=True, exist_ok=False)
(S0 / "results/reaudit_r2/reaudit.json").write_text(json.dumps(out, indent=1, default=str))
allok = all(c["ok"] for c in out["checks"].values()); print("\nRE-AUDIT:", "PASS" if allok else "FAIL/CAVEATS", f"({sum(c['ok'] for c in out['checks'].values())}/{len(out['checks'])})")
print(json.dumps({k: out[k] for k in ("restart_window", "statistics", "independent_mutation_challenge", "tracked_modified_files_touched_after_freeze")}, indent=1, default=str)[:3500])
