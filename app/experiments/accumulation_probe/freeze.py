"""Stage 0 FREEZE: record the full pre-run evidence (git, server, model+digest, code/artifact hashes, preregistration hash) into an immutable
FREEZE.json before the first model call. usage: python -I -B freeze.py --prereg <path-to-prereg.md> --verify-script <path>"""
import argparse, os, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import common, ollama_client
from app.experiments.accumulation_probe.common import EXP_ROOT, REPO, sha256_file, sha256_text, write_json_new
S0 = EXP_ROOT / "stage0"

def sh(cmd, cwd=REPO): return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}).stdout

def _rel(p):
    p = Path(p).resolve()
    try: return str(p.relative_to(REPO))
    except ValueError: return str(p)

def server_facts():
    pidf = REPO / "memory" / "echo_server.pid"
    if not pidf.exists(): return {"pid": None}
    pid = pidf.read_text().strip(); return {"pid": pid, "start": sh(["ps", "-o", "lstart=", "-p", pid]).strip(), "cmd": sh(["ps", "-o", "command=", "-p", pid]).strip()}

def frozen_files(root=None):
    root = Path(root) if root else S0; out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name not in ("calls.jsonl", "FREEZE.json", "FREEZE.sha256", "ABORT") and "grading" not in p.parts and "results" not in p.parts:
            out[str(p.relative_to(root))] = sha256_file(p)
    return out

def collect(prereg, verify_script):
    porc = sh(["git", "status", "--porcelain"])
    mi = ollama_client.model_info(common.OLLAMA_URL, common.MODEL)
    assert mi["found"] and mi["digest"], "model not found in Ollama"
    for rep in ("oracle_qualification", "leakage", "import_audit"):
        assert common.read_json(S0 / "reports" / f"{rep}.json")["ok"], f"{rep} not ok"
    assert all(j["ok"] for j in common.read_json(S0 / "reports" / "jail_probes.json")), "jail probes not ok"
    pkg = Path(__file__).parent
    from app.experiments.accumulation_probe import grade as _g
    text = Path(prereg).read_text(); consts = {n: getattr(_g, n) for n in ("HEADROOM_MIN", "HEADROOM_LOWER_MIN", "PER_CONV_HEADROOM", "N_CEILING", "NOISE_MAX", "MISMATCH_GAP_MIN", "REGRADE_AGREE_MIN", "INFRA_MAX", "TRUNC_MAX", "BOOT_N")}
    missing = [f"{n} = {v}" for n, v in consts.items() if f"{n} = {v}" not in text]
    assert not missing, f"preregistration text does not state these decision constants exactly: {missing}"
    return {"frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "protocol": "AP-0 Stage 0",
            "preregistration": {"path": _rel(prereg), "sha256": sha256_file(prereg)},
            "git": {"head": sh(["git", "rev-parse", "HEAD"]).strip(), "branch": sh(["git", "symbolic-ref", "-q", "HEAD"]).strip(),
                    "porcelain_lines": len(porc.splitlines()), "porcelain_sha256": sha256_text(porc)},
            "server": server_facts(), "model": mi,
            "options": common.OPTIONS, "master_seed": common.MASTER_SEED, "n_samples": common.N_SAMPLES, "n_shards": common.N_SHARDS,
            "python": {"path": common.PYTHON, "version": sh([common.PYTHON, "--version"]).strip() or sh([common.PYTHON, "--version"]),
                       "requests": sh([common.PYTHON, "-c", "import requests;print(requests.__version__)"]).strip()},
            "sandbox": {"profile_sha256": sha256_file(REPO / "sandbox" / "echo_sandbox.sb"), "wrapper_sha256": sha256_file(REPO / "sandbox" / "safe_exec_wrapper.py")},
            "code_sha256": {p.name: sha256_file(p) for p in sorted(pkg.glob("*.py"))},
            "verify_script": {"path": _rel(verify_script), "sha256": sha256_file(verify_script)},
            "artifact_sha256": frozen_files(), "arm_roots": {a: str((S0 / "runs" / a).resolve()) for a in common.ARMS}}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--prereg", required=True); ap.add_argument("--verify-script", required=True); a = ap.parse_args()
    if (S0 / "FREEZE.json").exists(): sys.exit("STOP: already frozen")
    f = collect(a.prereg, a.verify_script); write_json_new(S0 / "FREEZE.json", f)
    h = sha256_file(S0 / "FREEZE.json"); (S0 / "FREEZE.sha256").write_text(h + "  FREEZE.json\n")
    for p in S0.rglob("*"):
        if p.is_file() and ("oracle" in p.parts or "public" in p.parts or "reports" in p.parts or p.name in ("plan.json", "public_tasks.json", "FREEZE.json")): os.chmod(p, 0o444)
    print("FROZEN. FREEZE.json sha256 =", h); print("preregistration sha256 =", f["preregistration"]["sha256"]); print("git head =", f["git"]["head"], "porcelain =", f["git"]["porcelain_lines"])
    print("server =", f["server"]); print("model =", f["model"])
