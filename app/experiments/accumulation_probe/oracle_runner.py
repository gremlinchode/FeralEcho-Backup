"""Sandboxed grading + code extraction (stdlib only). Mirrors sandbox/run_script.run_sandbox_script_isolated's invocation
(same profile, same wrapper, same success rule) WITHOUT importing it (its import has file-writing side effects)."""
import os, re, subprocess, tempfile, time, secrets
from .common import REPO, PYTHON, SANDBOX_TIMEOUT_S

SANDBOX_PROFILE = str(REPO / "sandbox" / "echo_sandbox.sb")
SANDBOX_WRAPPER = str(REPO / "sandbox" / "safe_exec_wrapper.py")

def extract_code(raw: str, fn: str = None) -> str:
    """Pre-registered rule: the LAST fenced block that defines `def <fn>(` wins (fn = the requested function name); if none defines it, the last fenced
    block; if there is no fence, the raw text when it contains a def. Identical for every arm."""
    raw = raw or ""
    fences = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if fences:
        if fn:
            defs = [f for f in fences if f"def {fn}(" in f]
            if defs: return defs[-1].strip("\n") + "\n"
        return fences[-1].strip("\n") + "\n"
    if "def " in raw: return raw.strip("\n") + "\n"
    return ""

def run_script(source: str, timeout: int = SANDBOX_TIMEOUT_S) -> dict:
    t0 = time.time()
    try:
        with tempfile.TemporaryDirectory(prefix="ap0_sandbox_") as scratch:
            sc = os.path.realpath(scratch); path = os.path.join(sc, "_script.py")
            with open(path, "w") as f: f.write(source)
            p = subprocess.run(["sandbox-exec", "-f", SANDBOX_PROFILE, "-D", f"SCRATCH={sc}", PYTHON, SANDBOX_WRAPPER, sc, path, "--mode=script"],
                               capture_output=True, text=True, timeout=timeout, cwd=sc)
        out = p.stdout.strip()
        if p.returncode == 0 and "SANDBOX_OK" in p.stdout:
            return {"success": True, "output": out, "error": None, "duration": round(time.time() - t0, 3), "infra": False}
        err = (p.stderr.strip() or "sandbox exited non-zero")[:1500]
        infra = ("sandbox_apply" in err) or ("sandbox-exec" in err and "error" in err.lower() and "Traceback" not in err)
        return {"success": False, "output": out, "error": err, "duration": round(time.time() - t0, 3), "infra": infra}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": f"Timed out after {timeout}s", "duration": round(time.time() - t0, 3), "infra": False, "timeout": True}
    except Exception as e:                                           # harness-side failure, not the candidate's fault
        return {"success": False, "output": "", "error": f"{type(e).__name__}: {e}", "duration": round(time.time() - t0, 3), "infra": True}

def grade(candidate_code: str, test_code: str) -> dict:
    """PASS iff the sandbox ran the candidate + hidden tests to completion and the per-grade random nonce line was printed
    (a candidate cannot print it: the nonce is generated here, after generation)."""
    nonce = secrets.token_hex(8)
    res = run_script(candidate_code + "\n\n" + test_code.replace("@@NONCE@@", nonce))
    passed = res["success"] and ("ALL_TESTS_PASSED_" + nonce) in res["output"]
    return {"passed": bool(passed), "ran_ok": res["success"], "output_tail": res["output"][-300:], "error_tail": (res["error"] or "")[-300:],
            "infra": res.get("infra", False), "timeout": res.get("timeout", False), "duration": res["duration"]}
